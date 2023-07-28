def get_commit_message_prompt(git_diff_text):
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
                "content": git_diff_text,
            },
        ],
    }


def get_review_prompt(git_diff_text):
    return {
        "model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "temperature": 0.5,
        "n": 1,
        "stop": None,
        "messages": [
            {
                "role": "user",
                "content": "You are a code reviewer. You should review my code changes and provide feedback. "
                + "Provide feeback on how to improve the code. Provide feedback on potential bugs. "
                + "You will get my changes with line numbers at the start of each line. "
                + "Provide feedback as a json object with the following format: "
                + '{"filename":{"line_number":{"feedback: your feedback."},}}',
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
        "max_tokens": 2000,
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
