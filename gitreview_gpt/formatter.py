import re
import textwrap
import os
import json
import gitreview_gpt.utils as utils
from typing import Tuple, Dict, List


class CodeChunk:
    def __init__(self, start_line, end_line, code):
        self.start_line = start_line
        self.end_line = end_line
        self.code = code


class FileChunk:
    def __init__(self, file_name, file_path, code_chunks):
        self.file_name = file_name
        self.file_path = file_path
        self.code_chunks = code_chunks


# Format the git diff into a format that can be used by the GPT-3.5 API
# Add line numbers to the diff
# Split the diff into chunks per file
def format_git_diff(
    diff_text: str,
) -> Tuple[str, Dict[str, str], Dict[str, Dict[str, List[CodeChunk]]], Dict[str, str],]:
    git_diff_formatted = ""
    git_diff_file_chunks = {}
    git_diff_code_block_chunks = {}
    file_paths = {}

    file_blacklist = utils.get_file_blacklist()
    # Split git diff into chunks with separator +++ line inclusive,
    # the line with the filename
    parent_chunks = re.split(r"\n\+{3,}\s", diff_text, re.MULTILINE)
    for j, file_chunk in enumerate(parent_chunks, -1):
        # Skip first chunk (it's the head info)
        if j == -1:
            continue

        # Remove git --diff section
        file_chunk = re.sub(
            r"(diff --git.*\n)(.*\n)", lambda match: match.group(1), file_chunk
        )
        file_chunk = re.sub(r"^diff --git.*\n", "", file_chunk, flags=re.MULTILINE)

        # Split chunk into chunks with separator @@ -n,n +n,n @@ inclusive,
        # the changes in the file
        changes_per_file = re.split(r"(?=@@ -\d+,\d+ \+\d+,\d+ @@)", file_chunk)
        file_name = ""
        for i, code_change_chunk in enumerate(changes_per_file, 1):
            # Skip first chunk (it's the file name)
            if i == 1:
                file_name = code_change_chunk.rstrip("\n").rsplit("/", 1)[-1]
                # Skip unmerged added files
                if file_name == "null":
                    break
                if file_name in file_blacklist:
                    break
                git_diff_formatted += code_change_chunk.rsplit("/", 1)[-1]
                git_diff_file_chunks[file_name] = code_change_chunk.rsplit("/", 1)[-1]
                git_diff_code_block_chunks[file_name] = {}
                file_paths[file_name] = code_change_chunk[2:].rstrip("\n")
                continue

            # Extract the line numbers from the changes pattern
            pattern = r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@"
            match = re.findall(pattern, code_change_chunk)
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
            code_chunk_formatted = ""
            optional_selection_marker = ""
            for line in code_change_chunk.splitlines():
                if line.startswith("@@ -"):
                    git_diff_formatted += line + "\n"
                    chunk_formatted += line + "\n"
                    code_chunk_formatted += line + "\n"
                    # Extract selection marker
                    parts = line.split("def", 1)
                    if len(parts) > 1:
                        optional_selection_marker = parts[1].strip()
                    else:
                        optional_selection_marker = ""
                    continue
                if line.startswith("---"):
                    continue
                if line.startswith("-"):
                    continue
                else:
                    line_counter += 1

                new_line = str(line_counter) + " " + line + "\n"
                git_diff_formatted += new_line
                chunk_formatted += new_line

                if line.startswith("+"):
                    code_chunk_formatted += str(line_counter) + " " + line[1:] + "\n"
                else:
                    code_chunk_formatted += new_line

            code_chunk = CodeChunk(
                start_line=chunk_dividers[0]["new_start_line"],
                end_line=chunk_dividers[0]["new_end_line"]
                + chunk_dividers[0]["new_start_line"]
                - 1,
                code=code_chunk_formatted,
            )
            git_diff_file_chunks[file_name] += chunk_formatted
            if optional_selection_marker not in git_diff_code_block_chunks[file_name]:
                git_diff_code_block_chunks[file_name][optional_selection_marker] = [
                    code_chunk
                ]
            else:
                git_diff_code_block_chunks[file_name][optional_selection_marker].append(
                    code_chunk
                )

    return (
        git_diff_formatted,
        git_diff_file_chunks,
        git_diff_code_block_chunks,
        file_paths,
    )


# Extract markdown code blocks from text
def extract_content_from_markdown_code_block(markdown_code_block) -> str:
    pattern = r"```(?:[a-zA-Z0-9]+)?\n(.*?)```"
    match = re.search(pattern, markdown_code_block, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return markdown_code_block.strip()


# Extract multiple markdown code blocks from text
def extract_content_from_multiple_markdown_code_blocks(markdown_text) -> list:
    pattern = r"```(?:[a-zA-Z0-9]+)?\n(.*?)```"
    matches = re.findall(pattern, markdown_text, re.DOTALL)
    extracted_content = [match.strip() for match in matches]
    if len(extracted_content) == 0:
        extracted_content = [markdown_text.strip()]
    return extracted_content


def parse_review_result(review_result):
    return remove_unused_suggestions(json.loads(review_result))


def remove_unused_suggestions(review_result):
    # Function to check if feedback contains "not used" or "unused" etc
    def has_not_used_or_unused(feedback):
        return (
            "not used" in feedback.lower()
            or "unused" in feedback.lower()
            or "not being used" in feedback.lower()
            or "variable name" in feedback.lower()
            or "more descriptive" in feedback.lower()
            or "more specific" in feedback.lower()
            or "never used" in feedback.lower()
            or "into smaller functions" in feedback.lower()
            or "to a separate function" in feedback.lower()
            or "extracting the logic" in feedback.lower()
            or "extract the logic" in feedback.lower()
        )

    # Filter out the entries based on the condition
    return {
        file: {
            line: value
            for line, value in file_data.items()
            if not has_not_used_or_unused(value["feedback"])
        }
        for file, file_data in review_result.items()
    }


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
            if feedback_lines[entry]["suggestion"] is not None:
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


def get_review_suggestions_per_file_payload_from_json(review_json):
    suggestions = {}
    for line in review_json:
        suggestions[line] = review_json[line]["feedback"]
        if "suggestion" in review_json[line]:
            if review_json[line]["suggestion"] is not None:
                suggestions[line] += " " + review_json[line]["suggestion"]
    return suggestions


def parse_apply_review_per_code_hunk(code_changes, review_json, line_number_stack):
    line_number = line_number_stack.pop()
    hunk_review_payload = []
    for code_change_hunk in code_changes:
        review_per_chunk = {}
        while (
            code_change_hunk.start_line
            <= line_number
            < code_change_hunk.start_line + code_change_hunk.end_line
        ):
            review_per_chunk[line_number] = review_json[str(line_number)]

            if not line_number_stack:
                break
            line_number = line_number_stack.pop()

        if review_per_chunk:
            suggestions = {}
            for line in review_per_chunk:
                suggestions[line] = review_per_chunk[line]["feedback"]
            hunk_review_payload.append(
                {"code": code_change_hunk.code, "suggestions": suggestions}
            )

        if not line_number_stack:
            break
    return hunk_review_payload


def code_block_to_dict(code_block) -> Dict[int, str]:
    lines = code_block.strip().splitlines()
    parsed_code_block = {}
    current_line_number = 0

    for line in lines:
        parts = re.split(r"^(\d{1,4}:?)", line, maxsplit=1)
        parts = [part for part in parts if part]  # Remove empty parts from split

        if len(parts) > 1:
            number_part = parts[0]
            remaining_part = parts[1]
            if remaining_part.startswith(" "):
                remaining_part = remaining_part[1:]
            if remaining_part.startswith(" "):
                remaining_part = remaining_part[1:]
            if ":" in number_part:
                number_part = number_part[:-1]  # Remove colon and convert to int

            try:
                number = int(number_part)
            except ValueError:
                # TODO no line numbers specified. Need to be processed differently
                return {}

            current_line_number = number
            parsed_code_block[number] = remaining_part
        if len(parts) == 1:
            try:
                number_part = parts[0]
                if ":" in number_part:
                    number_part = number_part[:-1]  # Remove colon and convert to int

                number = int(number_part)

                current_line_number = number
                parsed_code_block[number] = ""
            except ValueError:
                # If the line doesn't start with a number, it belongs to the prev line
                parsed_code_block[current_line_number] += "\n" + parts[0]

    return parsed_code_block
