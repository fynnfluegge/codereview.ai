import json
import subprocess
import tiktoken


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


def get_programming_language(filename):
    language_mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".html": "HTML",
        ".css": "CSS",
        ".php": "PHP",
        ".rb": "Ruby",
        ".go": "Go",
        ".rs": "Rust",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".cs": "C#",
        ".m": "Objective-C",
        ".scala": "Scala",
        ".pl": "Perl",
        ".lua": "Lua",
        ".r": "R",
        ".ts": "TypeScript",
    }

    # Extract file extension from the filename
    file_extension = filename[filename.rfind(".") :].lower()

    if file_extension in language_mapping:
        return language_mapping[file_extension]
    else:
        return "Unknown"


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


def override_lines_in_file(file_path, lines_dict):
    try:
        with open(file_path, "r") as file:
            existing_lines = file.readlines()

        with open(file_path, "w") as file:
            for line_number, new_line_content in lines_dict.items():
                # Adjust line number to 0-based index
                line_index = line_number - 1

                if 0 <= line_index < len(existing_lines):
                    existing_lines[line_index] = new_line_content + "\n"

            file.writelines(existing_lines)
    except Exception as e:
        print("An error occurred:", str(e))
