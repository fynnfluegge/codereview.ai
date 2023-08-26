from enum import Enum


class GptModel(Enum):
    GPT_35 = 4096
    GPT_4 = 8192


def get_commit_message_prompt(git_diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 256,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "Here are my code changes. Provide a commit message for my changes. Provide only the commit message in your response."
                "Don't include any explanations in your response. The commit message should consist of a header and a body. ",
            },
            {
                "role": "assistant",
                "content": "Sure! Please share the code changes you made.",
            },
            {
                "role": "user",
                "content": git_diff_text,
            },
        ],
    }


def get_review_prompt(git_diff_text, max_tokens, gpt_model: GptModel):
    return {
        "model": gpt_model == GptModel.GPT_35 and "gpt-3.5-turbo" or "gpt-4",
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "You are a code reviewer. "
                "You should review my code changes and provide feedback. "
                "Provide feedback on how to improve the code. "
                "Don't provide feedback on code style. "
                "You will get my changes with line numbers at the start of each line. "
                "Provide feedback as a JSON object with the following format: "
                '{"filename":{"line_number":{"feedback": "your feedback."}}}',
            },
            {
                "role": "assistant",
                "content": "Sure! Please share the code changes you made.",
            },
            {
                "role": "user",
                "content": git_diff_text,
            },
        ],
    }


def get_review_repair_prompt(invalid_json, error, max_tokens, gpt_model: GptModel):
    return {
        "model": gpt_model == GptModel.GPT_35 and "gpt-3.5-turbo" or "gpt-4",
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "I have a JSON that fails to parse with Python's `json.loads()` function. "
                f"`json.loads()` throws the following error: {error}. "
                "You should fix the JSON. "
                "Provide only the fixed JSON in your response.",
            },
            {
                "role": "assistant",
                "content": "Sure! Please share the JSON.",
            },
            {
                "role": "user",
                "content": invalid_json,
            },
        ],
    }


def get_apply_review_for_file_prompt(
    code, review_comments, max_tokens, programming_language, gpt_model: GptModel
):
    return {
        "model": gpt_model == GptModel.GPT_35 and "gpt-3.5-turbo" or "gpt-4",
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": f"Review the following {programming_language} code and address the review comments below:\n"
                f"{programming_language} code:\n"
                "```\n"
                f"{code}"
                "```\n"
                "Review comments:\n"
                f"{review_comments}"
                "\n"
                f"Apply the necessary changes to the {programming_language} code based on the review comments and provide an updated version of the code with the improvements made."
                f"Provide only the updated {programming_language} code in your response. Don't include any explanations in your response.",
            },
        ],
    }


def get_apply_review_for_git_diff_chunk_promp(
    code_chunk, review_comments, max_tokens, programming_language, gpt_model: GptModel
):
    return {
        "model": gpt_model == GptModel.GPT_35 and "gpt-3.5-turbo" or "gpt-4",
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": f"Review the following {programming_language} code snippet and address the review comments below:\n"
                f"{programming_language} code:\n"
                "```\n"
                f"{code_chunk}"
                "```\n"
                "Review comments:\n"
                f"{review_comments}"
                "\n"
                f"Apply the necessary changes to the {programming_language} code based on the review comments. "
                "Add line numbers to the code to indicate where the changes should be made. "
                "Preserve the indentation of the code. "
                "Don't include any explanations in your response.",
            },
        ],
    }
