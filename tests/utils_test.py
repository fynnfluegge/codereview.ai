import unittest
import json
import gitreview_gpt.utils as utils


class TestUtils(unittest.TestCase):
    def test_repair_truncated_json(self):
        json_str = """{
            "formatter.py": {
                "23": {
                    "feedback": "Consider adding type hints to the function signature.",
                    "suggestion": "Add type hints to the `format_git_diff` function."
                },
                "26": {
                    "feedback": "Consider using a more descriptive variable name instead of `file_chunks`.",
                    "suggestion": "Rename the `file_chunks` variable to something more descriptive."
                },
                "29": {
                    "feedback": "Consider using a more descriptive variable name inst
        """
        expected_repaired_json = """{
            "formatter.py": {
                "23": {
                    "feedback": "Consider adding type hints to the function signature.",
                    "suggestion": "Add type hints to the `format_git_diff` function."
                },
                "26": {
                    "feedback": "Consider using a more descriptive variable name instead of `file_chunks`.",
                    "suggestion": "Rename the `file_chunks` variable to something more descriptive."
                }\n}\n}"""

        repaired_json = utils.repair_truncated_json(json_str)
        self.assertEqual(repaired_json, expected_repaired_json)
