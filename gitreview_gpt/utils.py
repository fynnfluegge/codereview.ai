import json


def parse_string_to_int(input_string):
    if "-" in input_string:
        # If the input_string contains a range
        start, _ = input_string.split("-")
        return int(start)
    else:
        # If the input_string contains only a single number
        return int(input_string)


def repair_truncated_json(json_str):
    try:
        # Attempt to load the JSON
        json_data = json.loads(json_str)
        return json_data
    except json.JSONDecodeError:
        # If loading fails, try to find the last valid JSON fragment
        last_valid_index = 0
        for i in range(len(json_str) - 1, -1, -1):
            partial_json = json_str[: i + 1]
            try:
                json.loads(partial_json + "\n}\n}")
                last_valid_index = i
                break
            except json.JSONDecodeError:
                pass

        if last_valid_index > 0:
            repaired_json = json_str[: last_valid_index + 1]
            return repaired_json + "\n}\n}"
        else:
            raise ValueError("Could not repair JSON")
