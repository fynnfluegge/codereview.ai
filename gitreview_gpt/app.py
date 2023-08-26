import os
import subprocess
import argparse
import sys
import gitreview_gpt.prompt as prompt
import gitreview_gpt.formatter as formatter
import gitreview_gpt.utils as utils
import gitreview_gpt.request as request
import gitreview_gpt.reviewer as reviewer


def get_git_diff(branch):
    """
    Return the code changes as a git diff
    """
    if not branch:
        command = ["git", "diff", "HEAD"]
    else:
        command = ["git", "diff", branch, "--cached"]

    git_diff = subprocess.run(command, capture_output=True, text=True)

    return git_diff.stdout


def print_review_from_response_json(feedback_json):
    """
    Process response json and draw output to console
    """
    print("✨ Review Result ✨")
    for file in feedback_json:
        if feedback_json[file]:
            print(formatter.draw_box(file, feedback_json[file]))
        else:
            print("No issues found in " + utils.get_bold_text(file))


def apply_review_to_file(
    api_key, file, file_path, review_json, code_change_chunks, guided, gpt_model
):
    """
    Apply review to file
    """
    if not utils.has_unstaged_changes(file_path):
        if review_json:
            apply_changes = False
            if guided:
                print(f"Apply changes to {utils.get_bold_text(file)}? (y/n)")
                apply_changes = input().lower() == "y"
            if not guided or apply_changes:
                reviewer.apply_review(
                    api_key,
                    os.path.abspath(file_path),
                    review_json,
                    code_change_chunks,
                    gpt_model,
                )
    else:
        print(
            f"⚠️  There are unstaged changes in {utils.get_bold_text(file)}. "
            + "Please commit or stage them. "
            + "Applying review changes skipped for now."
        )


def run():
    """
    Main function to run the script
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=["review", "commit"],
        help="Review changes (review) or create commit message (commit)",
    )
    parser.add_argument(
        "--branch", type=str, help="Review changes against a specific branch"
    )
    parser.add_argument(
        "--guided",
        action="store_true",
        help="Guided mode. "
        + "Ask for confirmation before reviewing and applying changes for each file.",
    )
    parser.add_argument(
        "--readonly",
        action="store_true",
        help="Readonly mode. Review changes without applying them to the files.",
    )
    parser.add_argument(
        "--gpt4", action="store_true", help="Use GPT-4 (default: GPT-3.5)"
    )

    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        sys.exit("OPENAI_API_KEY not found.")

    if not args.action:
        sys.exit()

    diff_text = None

    if args.action == "review":
        diff_text = get_git_diff(args.branch)
    elif args.action == "commit":
        diff_text = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True
        ).stdout

    if not diff_text:
        sys.exit("No git changes.")

    (
        formatted_diff,
        diff_file_chunks,
        code_change_chunks,
        file_paths,
    ) = formatter.format_git_diff(diff_text)

    if args.action == "review":
        gpt_model = prompt.GptModel.GPT_4 if args.gpt4 else prompt.GptModel.GPT_35

        for key, value in diff_file_chunks.items():
            review_file = False
            if args.guided:
                print(f"Review file {utils.get_bold_text(key)}? (y/n)")
                review_file = input().lower() == "y"
            if not args.guided or review_file:
                file_tokens = utils.count_tokens(value)
                if file_tokens > gpt_model.value - 1024:
                    print(
                        f"⚠️  The token count of {utils.get_bold_text(key)} exceeds "
                        + "the current limit for a file. Conder using the "
                        + f"{utils.get_bold_text('--gpt4')} flag."
                    )
                    continue
                review_json = reviewer.request_review(api_key, value, gpt_model, key)
                if review_json is not None:
                    print_review_from_response_json(review_json)
                    if not args.readonly:
                        for file_name, review in review_json.items():
                            apply_review_to_file(
                                api_key,
                                file_name,
                                file_paths[file_name],
                                review,
                                code_change_chunks[file_name],
                                args.guided,
                                gpt_model,
                            )

    elif args.action == "commit":
        payload = prompt.get_commit_message_prompt(formatted_diff)
        commit_message = request.send_request(
            api_key, payload, "Creating commit message..."
        )
        print("✨ Commit Message ✨")
        print(commit_message)
        print("Do you want to commit the changes? (y/n)")
        user_input = input().lower()

        if user_input == "y":
            commit_command = ["git", "commit", "-m", commit_message]
            subprocess.run(commit_command, capture_output=True, text=True)
