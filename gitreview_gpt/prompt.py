def get_commit_message_prompt(git_diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 256,
        "temperature": 0.2,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "Here are my code changes. Provide a commit message for my changes. Provide only the commit message in your response."
                + "Don't include any explanations in your response.",
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


def get_review_prompt(git_diff_text, max_tokens):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "You are a code reviewer. You should review my code changes and provide feedback. "
                + "Provide feeback on how to improve the code. "
                + "Don't provide feedback on code style. "
                + "You will get my changes with line numbers at the start of each line. "
                + "Provide feedback as a json object with the following format: "
                + '{"filename":{"line_number":{"feedback: your feedback.", "suggestion": "your suggestion"},}}',
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


def get_review_repair_prompt(invalid_json, error, max_tokens):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "I have a json that fails to parse with pythons `json.loads()` function. "
                + f"`json.loads()` throws the following error: {error}. "
                + "You should fix the json. "
                + "Provide only the fixed json in your response.",
            },
            {
                "role": "assistant",
                "content": "Sure! Please share the json.",
            },
            {
                "role": "user",
                "content": invalid_json,
            },
        ],
    }


def get_apply_review_prompt(code, review_comments, max_tokens):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": max_tokens,
        "temperature": 0.4,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "Review the following Python code and address the review comments below:\n"
                + "Python code:\n"
                + "```\n"
                + code
                + "\n"
                + "```\n"
                + "Review comments:\n"
                + review_comments
                + "\n"
                + "Apply the necessary changes to the Python code based on the review comments and provide an updated version of the code with the improvements made."
                + "Provide only the updated Python code in your response. Don't include any explanations in your response.",
            },
        ],
    }
