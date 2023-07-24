import os
import textwrap
import subprocess
import json
import tiktoken
import argparse
import re
from yaspin import yaspin


def get_git_diff(staged, branch):
    # Run git diff command and capture the output
    if not branch:
        command = ["git", "diff", "--cached"] if staged else ["git", "diff", "HEAD"]
    else:
        command = ["git", "diff", branch]

    git_diff = subprocess.run(command, capture_output=True, text=True)

    return git_diff.stdout


# Format the git diff into a format that can be used by the GPT-3 API
# - add line numbers to the diff
# - split the diff into chunks per file
def format_git_diff(diff_text):
    diff_formatted = ""
    file_chunks = {}
    file_names = {}

    # Split git diff into chunks with separator +++ line inclusive, the line with the filename
    pattern = r"(?=^(\+\+\+).*$)"
    parent_chunks = re.split(r"\n\+{3,}\s", diff_text, re.MULTILINE)
    for j, chunk in enumerate(parent_chunks, 0):
        # skip first chunk (it's the head info)
        if j == 0:
            continue

        # Remove git --diff section
        chunk = re.sub(r"(diff --git.*\n)(.*\n)", lambda match: match.group(1), chunk)
        chunk = re.sub(r"^diff --git.*\n", "", chunk, flags=re.MULTILINE)

        # Split chunk into chunks with separator @@ -n,n +n,n @@ inclusive, the changes in the file
        pattern = r"(?=@@ -\d+,\d+ \+\d+,\d+ @@)"
        chunks = re.split(pattern, chunk)
        for i, chunk in enumerate(chunks, 1):
            # skip first chunk (it's the file name)
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

    return diff_formatted, file_chunks, file_names


# return the number of tokens in a string
def count_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokenized = encoding.encode(text)
    return len(tokenized)


def get_commit_message_prompt(diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "Here are my code changes. Could you please create a short and precise commit message for me?",
            },
            {
                "role": "assistant",
                "content": "Sure! I'll be happy to help. Please share the code changes you made.",
            },
            {
                "role": "user",
                "content": diff_text,
            },
        ],
    }


def get_review_prompt(diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "You are a code reviewer. Here are my code changes. You should review them and provide feedback. "
                + "Provide feeback on how to improve the code. Provide feedback on potential bugs. "
                + "Provide feedback in the following format: $$$filename:lines:$$$feedback. For example, $$$main.py:10:$$$This line of code is not required. ",
            },
            {
                "role": "assistant",
                "content": "Sure! I'll be happy to help. Please share the code changes you made.",
            },
            {
                "role": "user",
                "content": diff_text,
            },
        ],
    }


def send_request(api_key, payload, spinner_text):
    # Convert payload to JSON string
    payload_json = json.dumps(payload).replace("'", r"'\''")

    # create spinner
    spinner = yaspin()
    spinner.text = spinner_text
    spinner.start()

    # Prepare the curl command
    curl_command = f'curl -X POST "https://api.openai.com/v1/chat/completions" -H "Authorization: Bearer {api_key}" -H "Content-Type: application/json" -d \'{payload_json}\''

    # Run the curl command and capture the output
    curl_output = subprocess.run(
        curl_command, shell=True, capture_output=True, text=True
    )

    # stop spinner
    spinner.stop()

    # Process the response
    if curl_output.returncode == 0:
        json_response = json.loads(curl_output.stdout)
        reviewSummary = (
            json_response["choices"][0]["message"]["content"]
            .encode()
            .decode("unicode_escape")
        )
        return reviewSummary
    else:
        return f"Error: {curl_output.stderr.strip()}"


def draw_box(filename, feedback_lines):
    max_length = max(
        len(f"{line['line']}: {line['feedback']}") for line in feedback_lines
    )
    max_length = os.get_terminal_size()[0] - 2
    border = "╭" + "─" * (max_length) + "╮"
    bottom_border = "│" + "─" * (max_length) + "│"
    filename_line = "│ " + filename.ljust(max_length - 1) + "│"
    result = [border, filename_line, bottom_border]

    for entry in feedback_lines:
        line_string = f"Line {entry['line']}: {entry['feedback']}"
        if len(line_string) > max_length - 2:
            wrapped_lines = textwrap.wrap(line_string, width=max_length - 2)
            result.append("│ " + wrapped_lines[0].ljust(max_length - 2) + " │")
            for wrapped_line in wrapped_lines[1:]:
                result.append("│ " + wrapped_line.ljust(max_length - 2) + " │")
        else:
            result.append("│ " + line_string.ljust(max_length - 2) + " │")

    result.append("╰" + "─" * (max_length) + "╯")
    return "\n".join(result)


def get_review_output_text(review_result):
    parsed_feedback = {}

    pattern = r"\$\$\$(.*?):(\d+).*?\$\$\$(.*)"
    matches = re.findall(pattern, review_result)

    for match in matches:
        filename = match[0]
        line_number = match[1]
        feedback = match[2].strip()

        if filename not in parsed_feedback:
            parsed_feedback[filename] = []

        parsed_feedback[filename].append({"line": line_number, "feedback": feedback})

    # Print the parsed feedback
    for filename, feedback_list in parsed_feedback.items():
        print(draw_box(filename, feedback_list))


def run():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=["review", "commit"],
        help="Review changes against main branch (review) or create commit message (commit)",
    )
    parser.add_argument("--staged", action="store_true", help="Review staged changes")
    parser.add_argument(
        "--branch", type=str, help="Review changes against a specific branch"
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("OPENAI_API_KEY not found.")
        exit()

    if not args.action:
        exit()

    diff_text = None

    # Get the Git diff
    if args.action == "review":
        diff_text = get_git_diff(args.staged, args.branch)

    if args.action == "commit":
        diff_text = get_git_diff(True, None)

    if not diff_text:
        if not args.staged:
            print("No staged git changes.")
        else:
            print("No git changes.")
        exit()

    formatted_diff, diff_file_chunks, file_names = format_git_diff(diff_text)

    token_count = count_tokens(formatted_diff)

    # Review the changes using OpenAI API
    if args.action == "review":
        review_files_separately = token_count > 1500

        if not review_files_separately and len(file_names) > 1:
            print("Do you want to let your changed files be reviewed separately? (y/n)")
            user_input = input()
            if user_input == "y":
                review_files_separately = True

        # Check if the token count exceeds the limit of 1500
        # if yes, review the files separately
        if review_files_separately:
            if token_count > 1500:
                print("Your changes exceed the token limit of 1500.")

            print("The Review will be splitted into multiple requests.")

            for index, (key, value) in enumerate(diff_file_chunks.items()):
                print(f"Review file {file_names[index]}? (y/n)")
                user_input = input()
                if user_input == "n":
                    continue

                chunk_token_count = count_tokens(value)
                if chunk_token_count > 1500:
                    print(
                        "TODO: token count exceeds 1500. Split file chunks into chunk of changes"
                    )
                    exit()
                prompt = get_review_prompt(value)
                review_result = send_request(api_key, prompt, "Reviewing...")
                # TODO send repair request if review result has bad wrong format
                print("✨ Review Result ✨")
                get_review_output_text(review_result)

        # Review the changes in one request
        else:
            prompt = get_review_prompt(formatted_diff)
            review_result = send_request(api_key, prompt, "Reviewing...")
            # TODO send repair request if review result has bad format
            print("✨ Review Result ✨")
            get_review_output_text(review_result)

    # Create a commit message using OpenAI API
    if args.action == "commit":
        prompt = get_commit_message_prompt(formatted_diff)
        review_result = send_request(api_key, prompt, "Creating commit message...")
        print("✨ Commit Message ✨")
        print(review_result)
        print("Do you want to commit the changes? (y/n)")
        user_input = input()

        if user_input == "y":
            # Commit the changes
            commit_command = ["git", "commit", "-m", review_result]
            git_commit = subprocess.run(commit_command, capture_output=True, text=True)
