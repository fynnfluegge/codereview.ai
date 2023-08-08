def get_commit_message_prompt(git_diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 512,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "Here are my code changes. Provide a commit message for my changes. Provide only the commit message in your response.",
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


def get_review_prompt(git_diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 1096,
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


def get_review_repair_prompt(invalid_json, error):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 1096,
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


def get_apply_review_prompt(code_changes_with_suggestions):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 1096,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "I have a file containing python code and code reviews as a json object in the following format: "
                + '{"code":"the python code", "reviews": { "line_number": "review" }}'
                + "You should apply the review to the code. "
                + "Provide the code with the review applied.",
            },
            {
                "role": "assistant",
                "content": "Sure! Please share the code changes you made.",
            },
            {
                "role": "user",
                "content": code_changes_with_suggestions,
            },
        ],
    }
