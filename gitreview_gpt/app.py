import os
import subprocess
import json
import tiktoken
import argparse
import gitreview_gpt.prompt as prompt
import gitreview_gpt.formatter as formatter
from yaspin import yaspin


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
        # TODO check if 'choices' available
        reviewSummary = (
            json_response["choices"][0]["message"]["content"]
            .encode()
            .decode("unicode_escape")
        )
        return reviewSummary
    else:
        return f"Error: {curl_output.stderr.strip()}"


# Retrieve review from openai completions api
# Process response and send repair request if json has invalid format
def request_review(api_key, code_to_review):
    payload = prompt.get_review_prompt(code_to_review)
    review_result = send_request(api_key, payload, "Reviewing...")
    try:
        review_json = formatter.parse_review_result(review_result)
    except ValueError:
        print(review_result)
        try:
            review_json = formatter.parse_repair_review(review_result)
        except ValueError as e:
            print("Review result has invalid format. It will be repaired.")
            payload = prompt.get_review_repair_prompt(review_result, e)
            review_result = send_request(api_key, payload, "Repairing...")
            review_json = formatter.parse_repair_review(review_result)

    print_review_from_response_json(review_json)
    return review_json


# Retrieve code changes from openai completions api
# for one specific file with the related review
def request_review_changes(
    api_key,
    file_path,
    review_json,
    file_diff,
    code_change_chunks,
):
    try:
        with open(file_path, "r") as file:
            content = file.read()
            file_lines = file.readlines()
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            tokens = len(encoding.encode(file_diff + "\n" + json.dumps(review_json)))
            # Create a stack from the review suggestions line numbers
            line_number_stack = []
            for line_number in reversed(review_json.keys()):
                line_number_stack.append(int(line_number))
            # Split requests into changes chunks by selection markers
            payload = []
            if tokens > 1500:
                pass
            # Do review changes in one request
            else:
                for code_changes in code_change_chunks.values():
                    if not line_number_stack:
                        break
                    # TODO separate code changes and reviews
                    code_changes_payload = formatter.parse_apply_review_per_code_hunk(
                        code_changes,
                        review_json,
                        line_number_stack,
                    )
                    if code_changes_payload:
                        payload.append(code_changes_payload)
            # TODO send review changes request
            # TODO apply reivew changes to file
            print(payload)

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except IOError:
        print(f"Error reading file '{file_path}'.")
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

            for index, value in enumerate(diff_file_chunks.values()):
                print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")
                user_input = input()
                if user_input == "n":
                    continue

                chunk_token_count = count_tokens(value)
                if chunk_token_count > 1500:
                    print(
                        "TODO: token count exceeds 1500. Split file chunks into chunk of changes"
                    )
                    exit()
                review_result = request_review(api_key, value)
                if review_result is not None:
                    request_review_changes(
                        api_key,
                        git_root + "/" + file_paths[index],
                        review_result[file_names[index]],
                        value,
                        code_change_chunks[index],
                    )

        # Review the changes in one request
        else:
            request_review(api_key, formatted_diff)

    # Create a commit message using OpenAI API
    if args.action == "commit":
        payload = prompt.get_commit_message_prompt(formatted_diff)
        review_result = send_request(api_key, payload, "Creating commit message...")
        print("✨ Commit Message ✨")
        print(review_result)
        print("Do you want to commit the changes? (y/n)")
        user_input = input()

        if user_input == "y":
            # Commit the changes
            commit_command = ["git", "commit", "-m", review_result]
            subprocess.run(commit_command, capture_output=True, text=True)
