import unittest
import json
import gitreview_gpt.formatter as formatter


class TestReviewParser(unittest.TestCase):
    def setUp(self):
        self.code_change_chunks = {
            "": [
                formatter.CodeChunk(
                    start_line=3,
                    end_line=6,
                    code="@@ -3,6 +3,7 @@ import subprocess\n"
                    + "3 import json\n"
                    + "4 import tiktoken\n"
                    + "5 import argparse\n"
                    + "6 + import requests\n"
                    + "7 import gitreview_gpt.prompt as prompt\n"
                    + "8 import gitreview_gpt.formatter as formatter\n"
                    + "9 from yaspin import yaspin\n",
                )
            ],
            "run():": [
                formatter.CodeChunk(
                    start_line=211,
                    end_line=8,
                    code="@@ -156,8 +211,8 @@ def run():\n"
                    + "211 \n"
                    + '212     print("The Review will be splitted into multiple requests.")\n'
                    + "213 \n"
                    + "214 +    for index, value in enumerate(diff_file_chunks.values()):\n"
                    + '215 +        print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")\n'
                    + "216          user_input = input()\n"
                    + '217          if user_input == "n":\n'
                    + "218              continue\n",
                ),
                formatter.CodeChunk(
                    start_line=223,
                    end_line=15,
                    code="@@ -168,7 +223,15 @@ def run():\n"
                    + '223          "TODO: token count exceeds 1500. Split file chunks into chunk of changes"\n'
                    + "224             )\n"
                    + "225             exit()\n"
                    + "226 +                review_result = request_review(api_key, value)\n"
                    + "227 +                # if review_result is not None:\n"
                    + "228 +                #     request_review_changes(\n"
                    + "229 +                #         api_key,\n"
                    + '230 +                #         git_root + " / " + file_paths[index],\n'
                    + "231 +                #         review_result[file_names[index]],\n"
                    + "232 +                #         value,\n"
                    + "233 +                #         code_change_chunks[index],\n"
                    + "234 +                #     )\n"
                    + "235 \n"
                    + "236      # Review the changes in one request\n"
                    + "237      else:\n",
                ),
                formatter.CodeChunk(
                    start_line=241,
                    end_line=3,
                    code="@@ -241,3 +241,4 @@ def run():\n"
                    + "241          )\n"
                    + "242          exit()\n"
                    + "243 \n"
                    + "244 +\n",
                ),
            ],
        }
        self.review_result = {
            "215": {"feedback": "Some feedback comments to line 215."},
            "225": {"feedback": "Some feedback comments to line 225."},
            "226": {"feedback": "Some feedback comments to line 226."},
            "232": {"feedback": "Some feedback comments to line 227."},
        }
        self.code_change_hunk_review_payload = [
            {
                "code": "@@ -156,8 +211,8 @@ def run():\n"
                + "211 \n"
                + '212     print("The Review will be splitted into multiple requests.")\n'
                + "213 \n"
                + "214 +    for index, value in enumerate(diff_file_chunks.values()):\n"
                + '215 +        print(f"Review file \x1b[01m{file_names[index]}\x1b[0m? (y/n)")\n'
                + "216          user_input = input()\n"
                + '217          if user_input == "n":\n'
                + "218              continue\n",
                "suggestions": {215: "Some feedback comments to line 215."},
            },
            {
                "code": "@@ -168,7 +223,15 @@ def run():\n"
                + '223          "TODO: token count exceeds 1500. Split file chunks into chunk of changes"\n'
                + "224             )\n"
                + "225             exit()\n"
                + "226 +                review_result = request_review(api_key, value)\n"
                + "227 +                # if review_result is not None:\n"
                + "228 +                #     request_review_changes(\n"
                + "229 +                #         api_key,\n"
                + '230 +                #         git_root + " / " + file_paths[index],\n'
                + "231 +                #         review_result[file_names[index]],\n"
                + "232 +                #         value,\n"
                + "233 +                #         code_change_chunks[index],\n"
                + "234 +                #     )\n"
                + "235 \n"
                + "236      # Review the changes in one request\n"
                + "237      else:\n",
                "suggestions": {
                    225: "Some feedback comments to line 225.",
                    226: "Some feedback comments to line 226.",
                    232: "Some feedback comments to line 227.",
                },
            },
        ]
        self.string_with_markdown_code_block = (
            "Here is some code:\n"
            + "```\n"
            + "def run():\n"
            + "    print('Hello World!')\n"
            + "```\n"
        )
        self.string_with_python_markdown_code_block = (
            "Here is some python code:\n"
            + "```python\n"
            + "def run():\n"
            + "    print('Hello World!')\n"
            + "```\n"
        )
        self.git_diff = (
            "Here is the git diff for the code changes based on the provided reviews:\n"
            + "```diff\n"
            + "diff --git a/README.md b/README.md\n"
            + "```"
        )

    def test_parse_apply_review_per_code_hunk(self):
        line_numbers = [232, 226, 225, 215]
        code_change_hunk_review_payload = formatter.parse_apply_review_per_code_hunk(
            self.code_change_chunks["run():"], self.review_result, line_numbers
        )
        self.assertEqual(
            code_change_hunk_review_payload, self.code_change_hunk_review_payload
        )
        self.assertEqual(line_numbers, [])

    def test_extract_content_from_markdown_code_block(self):
        content = formatter.extract_content_from_markdown_code_block(
            self.string_with_markdown_code_block
        )
        python_content = formatter.extract_content_from_markdown_code_block(
            self.string_with_python_markdown_code_block
        )
        git_diff = formatter.extract_content_from_markdown_code_block(self.git_diff)
        self.assertEqual(
            content,
            "def run():\n" + "    print('Hello World!')",
        )
        self.assertEqual(
            python_content,
            "def run():\n" + "    print('Hello World!')",
        )
        self.assertEqual(git_diff, "diff --git a/README.md b/README.md")
