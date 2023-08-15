import json
import subprocess
from yaspin import yaspin


def send_request(api_key, payload, spinner_text):
    """
    Send request with prompt as payload to OpenAI completions API.

    Args:
        api_key (str): The API key for authentication.
        payload (dict): The payload to send as JSON.
        spinner_text (str): The text to display in the spinner.

    Returns:
        str: The review summary if successful, or an error message if unsuccessful.
    """
    payload_json = json.dumps(payload).replace("'", r"'\''")

    spinner = yaspin()
    spinner.text = spinner_text
    spinner.start()

    curl_command = f'curl -X POST "https://api.openai.com/v1/chat/completions" -H "Authorization: Bearer {api_key}" -H "Content-Type: application/json" -d \'{payload_json}\''

    curl_output = subprocess.run(
        curl_command, shell=True, capture_output=True, text=True
    )

    spinner.stop()

    if curl_output.returncode == 0:
        json_response = json.loads(curl_output.stdout)
        try:
            review_summary = (
                json_response["choices"][0]["message"]["content"]
                .encode()
                .decode("unicode_escape")
            )
            return review_summary
        except KeyError:
            print(json_response["error"]["message"])
            return None
    else:
        return f"Error: {curl_output.stderr.strip()}"