import json
import subprocess
from yaspin import yaspin


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
        try:
            reviewSummary = (
                json_response["choices"][0]["message"]["content"]
                .encode()
                .decode("unicode_escape")
            )
            return reviewSummary
        except KeyError:
            print(json_response["error"]["message"])
            return None
    else:
        return f"Error: {curl_output.stderr.strip()}"
