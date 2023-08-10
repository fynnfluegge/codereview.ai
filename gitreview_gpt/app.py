import os
import subprocess
import json
import tiktoken
import argparse
import gitreview_gpt.prompt as prompt
import gitreview_gpt.formatter as formatter
from yaspin import yaspin
from typing import Dict, Any


# Return the code changes as a git diff
def get_git_diff(staged, branch):
    # Run git diff command and capture the output
    if not branch:
        command = ["git", "diff", "--cached"] if staged else ["git", "diff", "HEAD"]
    else:
        command = ["git", "diff", branch]

    git_diff = subprocess.run(command, capture_output=True, text=True)

    return git_diff.stdout


# Return the number of tokens in a string
def count_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokenized = encoding.encode(text)
    return len(tokenized)


# Send request with prompt as payload to openai completions api
def send_request(api_key, payload, spinner_text):
    # Convert payload to JSON string
    payload_json = json.dumps(payload).replace("'", r"'\''")

    # Create spinner
    spinner = yaspin()
    spinner.text = spinner_text
    spinner.start()

    # Prepare the curl command
    curl_command = f'curl -X POST "https://api.openai.com/v1/chat/completions" -H "Authorization: Bearer {api_key}" -H "Content-Type: application/json" -d \'{payload_json}\''

    # Run the curl command and capture the output
    curl_output = subprocess.run(
        curl_command, shell=True, capture_output=True, text=True
    )

    # Stop spinner
    spinner.stop()

    # Process the response
    if curl_output.returncode == 0:
        json_response = json.loads(curl_output.stdout)
        try:
            reviewSummary = (
                json_response["choices"][0]["message"]["content"]
                .encode()
                .decode("unicode_escape")
            )
            return reviewSummary
        except KeyError:
            print(json_response["error"]["message"])
            return None
    else:
        return f"Error: {curl_output.stderr.strip()}"


# Retrieve review from openai completions api
# Process response and send repair request if json has invalid format
def request_review(api_key, code_to_review) -> Dict[str, Any] | None:
    max_tokens = 4096 - count_tokens(
        json.dumps(prompt.get_review_prompt(code_to_review, 4096))
    )
    payload = prompt.get_review_prompt(code_to_review, max_tokens)
    review_result = send_request(api_key, payload, "Reviewing...")
    if not review_result:
        return None
    try:
        review_json = formatter.parse_review_result(review_result)
    except ValueError:
        try:
            review_json = formatter.parse_review_result(
                formatter.extract_content_from_markdown_code_block(review_result)
            )
        except ValueError as e:
            print("Review result has invalid format. It will be repaired.")
            payload = prompt.get_review_repair_prompt(review_result, e, max_tokens)
            review_result = send_request(api_key, payload, "Repairing...")
            review_json = formatter.parse_review_result(
                formatter.extract_content_from_markdown_code_block(review_result)
            )

    print_review_from_response_json(review_json)
    return review_json


# Retrieve code changes from openai completions api
# for one specific file with the related review
def apply_review_changes(
    api_key,
    file_path,
    review_json,
    git_diff_chunks=None,
):
    try:
        reviewed_git_diff = None
        with open(file_path, "r") as file:
            content = file.read()
            payload = {
                "code": content,
                "reviews": formatter.get_review_suggestions_per_file_payload_from_json(
                    review_json
                ),
            }
            prompt_payload = prompt.get_apply_review_prompt(
                content, json.dumps(payload["reviews"]), 4096
            )
            tokens = count_tokens(json.dumps(prompt_payload))
            max_completions_tokens = 4096 - tokens
            print(f"Tokens: {tokens}")
            if tokens > 2048 and git_diff_chunks is not None:
                line_number_stack = []
                for line_number in reversed(review_json.keys()):
                    line_number_stack.append(int(line_number))
                # Split requests into changes chunks by selection markers
                payload = []
                for git_chunk in git_diff_chunks.values():
                    print(git_chunk)
                    if not line_number_stack:
                        break
                    payload.append(
                        formatter.parse_apply_review_per_code_hunk(
                            git_chunk,
                            review_json,
                            line_number_stack,
                        )
                    )
                print(payload)
            else:
                reviewed_git_diff = send_request(
                    api_key,
                    prompt.get_apply_review_prompt(
                        content, json.dumps(payload["reviews"]), max_completions_tokens
                    ),
                    "Applying changes...",
                )
                reviewed_git_diff = formatter.extract_content_from_markdown_code_block(
                    reviewed_git_diff
                )
                file.close()
                with open(file_path, "w") as file:
                    if reviewed_git_diff:
                        file.write(reviewed_git_diff)

            # Call git apply using subprocess
            # try:
            #     current_directory = os.getcwd()
            #     repo_root = find_git_repo_root(current_directory)
            #     result = subprocess.run(
            #         [
            #             "git",
            #             "apply",
            #             "-",
            #         ],  # Use "-" to indicate reading diff from stdin
            #         input=reviewed_git_diff,  # Convert diff string to bytes
            #         cwd=repo_root,  # Set the working directory of the repo
            #         text=True,  # Interpret input and output as text
            #         stdout=subprocess.PIPE,
            #         stderr=subprocess.PIPE,
            #         check=True,  # Raise an error if the command returns a non-zero exit code
            #     )
            #     print("Git apply successful:", result.stdout)
            # except subprocess.CalledProcessError as e:
            #     print("Error applying Git diff:", e.stderr)

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except IOError:
        print(f"Error reading file '{file_path}'.")
    return None


def find_git_repo_root(path):
    while path != "/":
        if os.path.exists(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    return None


# Process response json and draw output to console
def print_review_from_response_json(feedback_json):
    print("✨ Review Result ✨")
    for file in feedback_json:
        print(formatter.draw_box(file, feedback_json[file]))


def run():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=["review", "commit"],
        help="Review changes (review) or create commit message (commit)",
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

    (
        formatted_diff,
        diff_file_chunks,
        code_change_chunks,
        file_names,
        file_paths,
    ) = formatter.format_git_diff(diff_text)
    token_count = count_tokens(formatted_diff)
    git_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], universal_newlines=True
    ).strip()

    # Review the changes using OpenAI API
    if args.action == "review":
        review_files_separately = token_count > 3072

        # Check if the token count exceeds the limit of 3072 (1024 tokens for response)
        # if yes, review the files separately
        if review_files_separately:
            print(
                "Your changes are large. The Review will be splitted into multiple requests."
            )

            # iterate over the file chunks in the git diff
            for index, value in enumerate(diff_file_chunks.values()):
                print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")
                user_input = input()
                if user_input == "n":
                    continue

                file_tokens = count_tokens(value)
                if file_tokens > 3072:
                    print(
                        "TODO: token count exceeds 2048 for a file. Split file changes into chunk of changes."
                    )
                    exit()
                review_result = request_review(api_key, value)
                if review_result is not None:
                    apply_review_changes(
                        api_key,
                        git_root + "/" + file_paths[index],
                        review_result[file_names[index]],
                        code_change_chunks[index],
                    )

        # Review the changes in one request
        else:
            review_result = request_review(api_key, formatted_diff)
            print(review_result)
            if review_result is not None:
                for file in review_result:
                    apply_review_changes(
                        api_key,
                        git_root + "/" + file,
                        review_result[file],
                    )

    # Create a commit message using OpenAI API
    if args.action == "commit":
        payload = prompt.get_commit_message_prompt(formatted_diff)
        commit_message = send_request(api_key, payload, "Creating commit message...")
        print("✨ Commit Message ✨")
        print(commit_message)
        print("Do you want to commit the changes? (y/n)")
        user_input = input()

        if user_input == "y":
            # Commit the changes
            commit_command = ["git", "commit", "-m", commit_message]
            subprocess.run(commit_command, capture_output=True, text=True)
