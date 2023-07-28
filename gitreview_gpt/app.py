import os
import subprocess
import json
import tiktoken
import argparse
import re
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
        get_review_output_from_response_json(review_result)
    except ValueError as e:
        print("Review result has bad format. It will be repaired.")
        payload = prompt.get_review_repair_prompt(review_result, e)
        review_result = send_request(api_key, payload, "Repairing...")
        print(review_result + "\n")
        pattern = r"json\s*({[^`]+})\s*"
        match = re.search(pattern, review_result, re.DOTALL)
        if match:
            get_review_output_from_response_json(match.group(1))
        else:
            get_review_output_from_response_json(review_result)


# Process response json and draw output to console
def get_review_output_from_response_json(feedback_json):
    feedback = json.loads(feedback_json)
    print("✨ Review Result ✨")
    for file in feedback:
        print(formatter.draw_box(file, feedback[file]))


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

    formatted_diff, diff_file_chunks, file_names = formatter.format_git_diff(diff_text)

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
                request_review(api_key, value)

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
