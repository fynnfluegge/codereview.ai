import re
import textwrap
import os


# Format the git diff into a format that can be used by the GPT-3.5 API
# Add line numbers to the diff
# Split the diff into chunks per file
def format_git_diff(diff_text):
    diff_formatted = ""
    file_chunks = {}
    file_names = {}

    # Split git diff into chunks with separator +++ line inclusive, the line with the filename
    pattern = r"(?=^(\+\+\+).*$)"
    parent_chunks = re.split(r"\n\+{3,}\s", diff_text, re.MULTILINE)
    for j, chunk in enumerate(parent_chunks, 0):
        # Skip first chunk (it's the head info)
        if j == 0:
            continue

        # Remove git --diff section
        chunk = re.sub(r"(diff --git.*\n)(.*\n)", lambda match: match.group(1), chunk)
        chunk = re.sub(r"^diff --git.*\n", "", chunk, flags=re.MULTILINE)

        # Split chunk into chunks with separator @@ -n,n +n,n @@ inclusive, the changes in the file
        pattern = r"(?=@@ -\d+,\d+ \+\d+,\d+ @@)"
        chunks = re.split(pattern, chunk)
        for i, chunk in enumerate(chunks, 1):
            # Skip first chunk (it's the file name)
            if i == 1:
                diff_formatted += chunk
                file_chunks[j] = chunk
                file_names[j - 1] = chunk.rstrip("\n").rsplit("/", 1)[-1]
                continue

            # Extract the line numbers from the changes pattern
            pattern = r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@"
            match = re.findall(pattern, chunk)
            chunk_dividers = []
            for m in match:
                chunk_dividers.append(
                    {
                        "original_start_line": int(m[0]),
                        "original_end_line": int(m[1]),
                        "new_start_line": int(m[2]),
                        "new_end_line": int(m[3]),
                    }
                )
            line_counter = -1 + chunk_dividers[0]["new_start_line"]

            chunk_formatted = ""
            for line in chunk.splitlines():
                if line.startswith("@@ -"):
                    diff_formatted += line + "\n"
                    chunk_formatted += line + "\n"
                    continue
                if line.startswith("---"):
                    continue
                if line.startswith("-"):
                    continue
                else:
                    line_counter += 1

                new_line = str(line_counter) + " " + line + "\n"
                diff_formatted += new_line
                chunk_formatted += new_line

            file_chunks[j] += chunk_formatted

    # TODO remove lines with pattern @@ -n,n +n,n @@ from diff_formatted and file_chunks
    return diff_formatted, file_chunks, file_names


# Draw review output box
def draw_box(filename, feedback_lines):
    max_length = os.get_terminal_size()[0] - 2
    border = "╭" + "─" * (max_length) + "╮"
    bottom_border = "│" + "─" * (max_length) + "│"
    filename_line = "│ " + filename.ljust(max_length - 1) + "│"
    result = [border, filename_line, bottom_border]

    for entry in feedback_lines:
        line_string = (
            f"◇ \033[01mLine {entry}\033[0m: {feedback_lines[entry]['feedback']}"
        )
        if "suggestion" in feedback_lines[entry]:
            line_string += f" {feedback_lines[entry]['suggestion']}"
        if len(line_string) > max_length - 2:
            wrapped_lines = textwrap.wrap(line_string, width=max_length - 4)
            result.append("│ " + wrapped_lines[0].ljust(max_length + 7) + " │")
            for wrapped_line in wrapped_lines[1:]:
                result.append("│   " + wrapped_line.ljust(max_length - 4) + " │")
        else:
            result.append("│ " + line_string.ljust(max_length + 7) + " │")

    result.append("╰" + "─" * (max_length) + "╯")
    return "\n".join(result)
