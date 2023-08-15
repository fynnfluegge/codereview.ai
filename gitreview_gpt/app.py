import os
import subprocess
import argparse
import gitreview_gpt.prompt as prompt
import gitreview_gpt.formatter as formatter
import gitreview_gpt.utils as utils
import gitreview_gpt.request as request
import gitreview_gpt.reviewer as reviewer


# Return the code changes as a git diff
def get_git_diff(staged, branch):
    if not branch:
        command = ["git", "diff", "--cached"] if staged else ["git", "diff", "HEAD"]
    else:
        command = ["git", "diff", branch]

    git_diff = subprocess.run(command, capture_output=True, text=True)

    return git_diff.stdout


# Process response json and draw output to console
def print_review_from_response_json(feedback_json):
    print("✨ Review Result ✨")
    for file in feedback_json:
        if feedback_json[file]:
            print(formatter.draw_box(file, feedback_json[file]))
        else:
            print("No issues found in " + file)


def apply_review_to_file(api_key, review_json, file_paths, code_change_chunks):
    if review_json is not None:
        print_review_from_response_json(review_json)
        if not utils.has_unstaged_changes():
            for index, file in enumerate(review_json):
                if review_json[file]:
                    reviewer.apply_review(
                        api_key,
                        os.path.abspath(file_paths[index]),
                        review_json[file],
                        code_change_chunks[index],
                    )
        else:
            print(
                "There are unstaged changes. Please commit or stage them before applying the review changes."
            )


def run():
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
    # parser.add_argument(
    #     "--gpt4", action="store_true", help="Use GPT-4 (default: GPT-3)"
    # )
    # parser.add_argument("--autonomous", action="store_true", help="Autonomous mode")

    # Parse the command-line arguments
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("OPENAI_API_KEY not found.")
        exit()

    if not args.action:
        exit()

    diff_text = None

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

    git_diff_token_count = utils.count_tokens(formatted_diff)

    if args.action == "review":
        review_files_separately = git_diff_token_count > 3072

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

                file_tokens = utils.count_tokens(value)
                if file_tokens > 3072:
                    print(
                        "TODO: token count exceeds 3072 for a file. Split file changes into chunk of changes."
                    )
                    exit()
                review_json = reviewer.request_review(api_key, value)
                apply_review_to_file(
                    api_key,
                    review_json,
                    [file_paths[index]],
                    [code_change_chunks[index]],
                )

        # Review the changes in one request
        else:
            review_json = reviewer.request_review(api_key, formatted_diff)
            apply_review_to_file(api_key, review_json, file_paths, code_change_chunks)

    # Create a commit message using OpenAI API
    if args.action == "commit":
        payload = prompt.get_commit_message_prompt(formatted_diff)
        commit_message = request.send_request(
            api_key, payload, "Creating commit message..."
        )
        print("✨ Commit Message ✨")
        print(commit_message)
        print("Do you want to commit the changes? (y/n)")
        user_input = input()

        if user_input == "y":
            # Commit the changes
            commit_command = ["git", "commit", "-m", commit_message]
            subprocess.run(commit_command, capture_output=True, text=True)
