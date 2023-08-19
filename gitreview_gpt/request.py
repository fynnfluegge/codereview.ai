import requests
from yaspin import yaspin


def send_request(api_key, payload, spinner_text):
    spinner = yaspin(text=spinner_text)
    spinner.start()

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        json_response = response.json()
        review_summary = (
            json_response["choices"][0]["message"]["content"]
            .encode()
            .decode("unicode_escape")
        )
        return review_summary
    except (KeyError, requests.exceptions.RequestException) as e:
        print("💥 An error occurred while requesting a review.")
        print(str(e))
        return None
    finally:
        spinner.stop()
