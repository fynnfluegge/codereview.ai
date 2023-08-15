import json
import os
from typing import Any, Dict
import gitreview_gpt.prompt as prompt
import gitreview_gpt.formatter as formatter
import gitreview_gpt.utils as utils
import gitreview_gpt.request as request


# Retrieve review from openai completions api
# Process response and send repair request if json has invalid format
def request_review(api_key, code_to_review) -> Dict[str, Any] | None:
    max_tokens = 4096 - utils.count_tokens(
        json.dumps(prompt.get_review_prompt(code_to_review, 4096))
    )
    payload = prompt.get_review_prompt(code_to_review, max_tokens)
    review_result = request.send_request(api_key, payload, "Reviewing...")
    if not review_result:
        return None
    try:
        review_json = formatter.parse_review_result(review_result)
    except ValueError:
        try:
            # Try to parse review result from marldown code block
            review_json = formatter.parse_review_result(
                formatter.extract_content_from_markdown_code_block(review_result)
            )
        except ValueError:
            try:
                # Try to repair truncated review result
                review_json = formatter.parse_review_result(
                    utils.repair_truncated_json(review_result)
                )
            except ValueError as e:
                try:
                    print("Review result has invalid format. It will be repaired.")
                    payload = prompt.get_review_repair_prompt(
                        review_result, e, max_tokens
                    )
                    review_result = request.send_request(
                        api_key, payload, "Repairing... 🔧"
                    )
                    review_json = formatter.parse_review_result(
                        formatter.extract_content_from_markdown_code_block(
                            review_result
                        )
                    )
                except ValueError:
                    print("Review result could not be repaired.")
                    print(review_result)
                    print("Feel free to create an issue on GitHub.")
                    return None

    return review_json


# Retrieve code changes from openai completions api
# for one specific file with the related review
def apply_review(
    api_key,
    absolute_file_path,
    review_json,
    selection_marker_chunks=None,
):
    try:
        with open(absolute_file_path, "r") as file:
            programming_language = utils.get_programming_language(file.name)
            file_content = file.read()
            payload = {
                "code": file_content,
                "reviews": formatter.get_review_suggestions_per_file_payload_from_json(
                    review_json
                ),
            }
            prompt_payload = prompt.get_apply_review_for_file_prompt(
                file_content, json.dumps(payload["reviews"]), 4096, programming_language
            )
            tokens = utils.count_tokens(json.dumps(prompt_payload))
            # tokens for file content and review suggestions are greater than threshold
            # split requests into code chunks by selection markers
            if tokens > 1024 and selection_marker_chunks is not None:
                # initialize reviewed code for applying code changes later a tonce
                reviewed_code = []
                # create line number stack for  merging code chunk with line numbers
                line_number_stack = []
                for line_number in reversed(review_json.keys()):
                    line_number_stack.append(utils.parse_string_to_int(line_number))
                # Split requests into changes chunks by selection markers
                current_payload = []
                # Initialize current tokens with tokens for prompt payload
                # with empty code chunks and review suggestions
                current_tokens = utils.count_tokens(
                    json.dumps(
                        prompt.get_apply_review_for_file_prompt(
                            "",
                            "",
                            4096,
                            programming_language,
                        )
                    )
                )
                initial_tokens = current_tokens
                for code_chunk in selection_marker_chunks.values():
                    # if there are no more line numbers in stack,
                    # there are no more review suggestions, break loop
                    if not line_number_stack:
                        break

                    # merge code chunk with suggestions by line numbers
                    chunk_payload = formatter.parse_apply_review_per_code_hunk(
                        code_chunk,
                        review_json,
                        line_number_stack,
                    )

                    # there are review suggestions in that code chunk
                    if chunk_payload:
                        chunk_tokens = utils.count_tokens(json.dumps(chunk_payload))

                        # if the chunk is too big to be sent in one request
                        # send request for each code chunk of selection marker
                        if chunk_tokens + initial_tokens > 1024:
                            for chunk in chunk_payload:
                                # split into code_chunk_chunks
                                # print(chunk["code"])
                                # print(chunk["suggestions"])
                                # print("chunk_tokens: " + str(chunk_tokens))
                                # print("TODO: split chunk into smaller chunks")
                                pass

                        # else merge chunk with current payload if
                        # merged tokens still under threshold
                        if current_tokens + chunk_tokens < 1024:
                            current_tokens += chunk_tokens
                            current_payload.extend(chunk_payload)

                        # else send request for current payload
                        # and initialize new payload with current chunk afterwards
                        else:
                            if current_payload:
                                reviewed_code_chunks = request_review_changes(
                                    current_payload, api_key, programming_language
                                )
                                add_reviewed_code(reviewed_code_chunks, reviewed_code)
                                current_payload = []
                                current_payload.extend(chunk_payload)
                                current_tokens = chunk_tokens + initial_tokens

                # If there are still code chunks in current payload
                # send final request
                if current_payload:
                    reviewed_code_chunks = request_review_changes(
                        current_payload, api_key, programming_language
                    )
                    add_reviewed_code(reviewed_code_chunks, reviewed_code)

                file.close()
                code_lines: Dict[int, str] = formatter.code_block_to_dict(
                    "".join(reviewed_code)
                )
                print("".join(reviewed_code))
                print("---------------")
                print(code_lines)
                utils.override_lines_in_file(absolute_file_path, code_lines)
                print(
                    "Successfully applied review changes "
                    + f"{os.path.basename(absolute_file_path)} ✅"
                )

            # tokens for file content and review suggestions are less than threshold
            # send request for file content and review suggestions
            else:
                max_completions_tokens = 4096 - tokens
                reviewed_git_diff = request.send_request(
                    api_key,
                    prompt.get_apply_review_for_file_prompt(
                        file_content,
                        json.dumps(payload["reviews"]),
                        max_completions_tokens,
                        programming_language,
                    ),
                    "Applying changes... 🔧",
                )
                reviewed_git_diff = formatter.extract_content_from_markdown_code_block(
                    reviewed_git_diff
                )
                file.close()
                with open(absolute_file_path, "w") as file:
                    if reviewed_git_diff:
                        file.write(reviewed_git_diff)
                        print(
                            "Successfully applied review changes "
                            + f"{os.path.basename(absolute_file_path)} ✅"
                        )

    except FileNotFoundError:
        print(f"File '{absolute_file_path}' not found.")
    except IOError:
        print(f"Error reading file '{absolute_file_path}'.")
    except ValueError as e:
        print(f"Error while applying review changes for file {absolute_file_path}.")
        print(e)
    return None


def request_review_changes(code_with_suggestions, api_key, programming_language):
    (
        code_chunk,
        suggestions,
    ) = formatter.merge_code_chunks_and_suggestions(code_with_suggestions)

    message_tokens = utils.count_tokens(
        json.dumps(
            prompt.get_apply_review_for_git_diff_chunk_promp(
                code_chunk,
                json.dumps(suggestions),
                4096,
                programming_language,
            )
        )
    )
    return request.send_request(
        api_key,
        prompt.get_apply_review_for_git_diff_chunk_promp(
            code_chunk,
            json.dumps(suggestions),
            4096 - message_tokens,
            programming_language,
        ),
        "Applying changes... 🔧",
    )


def add_reviewed_code(review_applied, reviewed_code):
    if review_applied:
        for (
            improved_code_block
        ) in formatter.extract_content_from_multiple_markdown_code_blocks(
            review_applied
        ):
            reviewed_code.append("\n" + improved_code_block)
