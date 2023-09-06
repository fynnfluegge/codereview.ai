import json
import subprocess
import tiktoken
import os
import re
from gitreview_gpt.constants import Language


def parse_string_to_int(input_string):
    if "-" in input_string:
        # If the input_string contains a range
        start, _ = input_string.split("-")
        return int(start)
    else:
        # If the input_string contains only a single number
        return int(input_string)


def repair_truncated_json(json_str):
    try:
        # Attempt to load the JSON
        json_data = json.loads(json_str)
        return json_data
    except json.JSONDecodeError:
        # If loading fails, try to find the last valid JSON fragment
        last_valid_index = 0
        for i in range(len(json_str) - 1, -1, -1):
            partial_json = json_str[: i + 1]
            try:
                json.loads(partial_json + "\n}\n}")
                last_valid_index = i
                break
            except json.JSONDecodeError:
                pass

        if last_valid_index > 0:
            repaired_json = json_str[: last_valid_index + 1]
            return repaired_json + "\n}\n}"
        else:
            raise ValueError("Could not repair JSON")


def get_programming_language(file_extension: str) -> Language:
    """
    Retrieves the programming language based on the given file extension.

    Args:
        file_extension (str): The file extension to determine the programming language.

    Returns:
        Language: The programming language associated with the given file extension.
    """
    language_mapping = {
        ".py": Language.PYTHON,
        ".js": Language.JAVASCRIPT,
        ".ts": Language.TYPESCRIPT,
        ".java": Language.JAVA,
        ".kt": Language.KOTLIN,
        ".lua": Language.LUA,
        ".rs": Language.RUST,
        ".go": Language.GO,
    }
    return language_mapping.get(file_extension, Language.UNKNOWN)


def get_file_extension(file_name: str) -> str:
    """
    Return the extension of the file.

    Parameters:
    file_name (str): The name of the file.

    Returns:
    str: The file extension.
    """
    return os.path.splitext(file_name)[-1]


def get_file_blacklist():
    return [
        ".git",
        "package-lock.json",
        "package.json",
        "yarn.lock",
        "pom.xml",
        "build.gradle",
        "pyproject.toml",
        "requirements.txt",
        "poetry.lock",
        "tsconfig.json",
        "pnpm-lock.yaml",
    ]


# Return the number of tokens in a string
def count_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokenized = encoding.encode(text)
    return len(tokenized)


def get_bold_text(text):
    return f"\033[01m{text}\033[0m"


def get_git_repo_root():
    return subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], universal_newlines=True
    ).strip()


def has_unstaged_changes(file):
    try:
        # Run the "git diff --quiet" command and capture its output
        subprocess.check_output(["git", "diff", "--quiet", file])
        return False  # No unstaged changes
    except subprocess.CalledProcessError:
        return True  # Unstaged changes exist


def write_code_snippet_to_file(file_path: str, original_code: str, modified_code: str):
    """
    Replace the original code snippet with the modified code in the given file.

    Args:
        file_path (str): The path to the file.
        original_code (str): The code snippet to be replaced.
        modified_code (str): The code snippet to replace the original code.

    Returns:
        None
    """
    with open(file_path, "r") as file:
        file_content = file.read()
        start_pos = file_content.find(original_code)
        if start_pos != -1:
            end_pos = start_pos + len(original_code)
            indentation = file_content[:start_pos].split("\n")[-1]
            modeified_lines = modified_code.split("\n")
            indented_modified_lines = [indentation + line for line in modeified_lines]
            indented_modified_code = "\n".join(indented_modified_lines)
            modified_content = (
                file_content[:start_pos].rstrip()
                + "\n"
                + indented_modified_code
                + file_content[end_pos:]
            )
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(modified_content)


def extract_content_from_markdown_code_block(markdown_code_block) -> str:
    """
    Extracts the content from a markdown code block inside a string.

    Args:
        markdown_code_block (str): The markdown code block to extract content from.

    Returns:
        str: The extracted content.

    """
    pattern = r"```(?:[a-zA-Z0-9]+)?\n(.*?)```"
    match = re.search(pattern, markdown_code_block, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return markdown_code_block.strip()


def get_start_line_number(content, line):
    """
    Returns the starting line number of the given line in the content.

    Args:
        content (str): The content to search in.
        line (str): The line to search for.

    Returns:
        int: The starting line number of the given line in the content.
    """
    lines = content.split("\n")
    for i, l in enumerate(lines):
        if l == line:
            return i + 1
    return -1


def add_line_numbers(code_string, start_number=1):
    # Split the code into lines
    lines = code_string.split("\n")

    # Calculate the width of the line number column based on the number of lines
    line_number_width = len(str(len(lines) + start_number - 1))

    # Create a list to store lines with line numbers
    lines_with_numbers = []

    # Iterate through the lines and add line numbers
    for i, line in enumerate(lines, start=start_number):
        line_number = str(i).rjust(line_number_width)  # Right-align line numbers
        lines_with_numbers.append(f"{line_number}: {line}")

    # Join the lines with line numbers and return as a single string
    code_with_line_numbers = "\n".join(lines_with_numbers)

    return code_with_line_numbers
