import unittest
import gitreview_gpt.formatter as formatter


class TestFormatter(unittest.TestCase):
    def setUp(self):
        self.git_diff = (
            "diff --git a/gitreview_gpt/app.py b/gitreview_gpt/app.py\n"
            + "index a18d784..49f9b9e 100644\n"
            + "--- a/gitreview_gpt/app.py\n"
            + "+++ b/gitreview_gpt/app.py\n"
            + "@@ -3,7 +3,6 @@ import subprocess\n"
            + "import json\n"
            + "import tiktoken\n"
            + "import argparse\n"
            + "-import re\n"
            + "import gitreview_gpt.prompt as prompt\n"
            + "import gitreview_gpt.formatter as formatter\n"
            + "from yaspin import yaspin\n"
            + "@@ -156,8 +211,8 @@ def run():\n"
            + "\n"
            + '    print("The Review will be splitted into multiple requests.")\n'
            + "\n"
            + "-    for index, (key, value) in enumerate(diff_file_chunks.items()):\n"
            + '-        print(f"Review file {file_names[index]}? (y/n)")\n'
            + "+    for index, value in enumerate(diff_file_chunks.values()):\n"
            + '+        print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")\n'
            + "         user_input = input()\n"
            + '         if user_input == "n":\n'
            + "             continue\n"
            + "@@ -168,7 +223,15 @@ def run():\n"
            + '         "TODO: token count exceeds 1500. Split file chunks into chunk of changes"\n'
            + "            )\n"
            + "            exit()\n"
            + "-                request_review(api_key, value)\n"
            + "+                review_result = request_review(api_key, value)\n"
            + "+                # if review_result is not None:\n"
            + "+                #     request_review_changes(\n"
            + "+                #         api_key,\n"
            + '+                #         git_root + " / " + file_paths[index],\n'
            + "+                #         review_result[file_names[index]],\n"
            + "+                #         value,\n"
            + "+                #         code_change_chunks[index],\n"
            + "+                #     )\n"
            + "\n"
            + "     # Review the changes in one request\n"
            + "     else:\n"
            + "diff --git a/gitreview_gpt/formatter.py b/gitreview_gpt/formatter.py\n"
            + "index 4ca0287..fbaed29 100644\n"
            + "--- a/gitreview_gpt/formatter.py\n"
            + "+++ b/gitreview_gpt/formatter.py\n"
            + "@@ -1,6 +1,18 @@\n"
            + "import re\n"
            + "import textwrap\n"
            + "import os\n"
            + "+import json\n"
            + "+\n"
            + "+\n"
            + "+class CodeChunk:\n"
            + "+    start_line: int\n"
            + "+    end_line: int\n"
            + "+    code: str\n"
            + "+\n"
            + "+    def __init__(self, start_line, end_line, code):\n"
            + "+        self.start_line = start_line\n"
            + "+        self.end_line = end_line\n"
            + "+        self.code = code\n"
            + "\n"
            + "\n"
            + "# Format the git diff into a format that can be used by the GPT-3.5 API\n"
        )
        self.git_diff_formatted_fixture = (
            "app.py\n"
            + "@@ -3,7 +3,6 @@ import subprocess\n"
            + "3 import json\n"
            + "4 import tiktoken\n"
            + "5 import argparse\n"
            + "6 import gitreview_gpt.prompt as prompt\n"
            + "7 import gitreview_gpt.formatter as formatter\n"
            + "8 from yaspin import yaspin\n"
            + "@@ -156,8 +211,8 @@ def run():\n"
            + "211 \n"
            + '212     print("The Review will be splitted into multiple requests.")\n'
            + "213 \n"
            + "214 +    for index, value in enumerate(diff_file_chunks.values()):\n"
            + '215 +        print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")\n'
            + "216          user_input = input()\n"
            + '217          if user_input == "n":\n'
            + "218              continue\n"
            + "@@ -168,7 +223,15 @@ def run():\n"
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
            + "237      else:\n"
            + "formatter.py\n"
            + "@@ -1,6 +1,18 @@\n"
            + "1 import re\n"
            + "2 import textwrap\n"
            + "3 import os\n"
            + "4 +import json\n"
            + "5 +\n"
            + "6 +\n"
            + "7 +class CodeChunk:\n"
            + "8 +    start_line: int\n"
            + "9 +    end_line: int\n"
            + "10 +    code: str\n"
            + "11 +\n"
            + "12 +    def __init__(self, start_line, end_line, code):\n"
            + "13 +        self.start_line = start_line\n"
            + "14 +        self.end_line = end_line\n"
            + "15 +        self.code = code\n"
            + "16 \n"
            + "17 \n"
            + "18 # Format the git diff into a format that can be used by the GPT-3.5 API\n"
        )

        self.file_chunks_fixture = {
            "app.py": "app.py\n"
            + "@@ -3,7 +3,6 @@ import subprocess\n"
            + "3 import json\n"
            + "4 import tiktoken\n"
            + "5 import argparse\n"
            + "6 import gitreview_gpt.prompt as prompt\n"
            + "7 import gitreview_gpt.formatter as formatter\n"
            + "8 from yaspin import yaspin\n"
            + "@@ -156,8 +211,8 @@ def run():\n"
            + "211 \n"
            + '212     print("The Review will be splitted into multiple requests.")\n'
            + "213 \n"
            + "214 +    for index, value in enumerate(diff_file_chunks.values()):\n"
            + '215 +        print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")\n'
            + "216          user_input = input()\n"
            + '217          if user_input == "n":\n'
            + "218              continue\n"
            + "@@ -168,7 +223,15 @@ def run():\n"
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
            "formatter.py": "formatter.py\n"
            + "@@ -1,6 +1,18 @@\n"
            + "1 import re\n"
            + "2 import textwrap\n"
            + "3 import os\n"
            + "4 +import json\n"
            + "5 +\n"
            + "6 +\n"
            + "7 +class CodeChunk:\n"
            + "8 +    start_line: int\n"
            + "9 +    end_line: int\n"
            + "10 +    code: str\n"
            + "11 +\n"
            + "12 +    def __init__(self, start_line, end_line, code):\n"
            + "13 +        self.start_line = start_line\n"
            + "14 +        self.end_line = end_line\n"
            + "15 +        self.code = code\n"
            + "16 \n"
            + "17 \n"
            + "18 # Format the git diff into a format that can be used by the GPT-3.5 API\n",
        }
        self.code_change_chunks_fixture = {
            "app.py": {
                "": [
                    formatter.CodeChunk(
                        start_line=3,
                        end_line=6,
                        code="@@ -3,7 +3,6 @@ import subprocess\n"
                        + "3 import json\n"
                        + "4 import tiktoken\n"
                        + "5 import argparse\n"
                        + "6 import gitreview_gpt.prompt as prompt\n"
                        + "7 import gitreview_gpt.formatter as formatter\n"
                        + "8 from yaspin import yaspin\n",
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
                        + "214     for index, value in enumerate(diff_file_chunks.values()):\n"
                        + '215         print(f"Review file \033[01m{file_names[index]}\033[0m? (y/n)")\n'
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
                        + "226                 review_result = request_review(api_key, value)\n"
                        + "227                 # if review_result is not None:\n"
                        + "228                 #     request_review_changes(\n"
                        + "229                 #         api_key,\n"
                        + '230                 #         git_root + " / " + file_paths[index],\n'
                        + "231                 #         review_result[file_names[index]],\n"
                        + "232                 #         value,\n"
                        + "233                 #         code_change_chunks[index],\n"
                        + "234                 #     )\n"
                        + "235 \n"
                        + "236      # Review the changes in one request\n"
                        + "237      else:\n",
                    ),
                ],
            },
            "formatter.py": {
                "": [
                    formatter.CodeChunk(
                        start_line=1,
                        end_line=18,
                        code="@@ -1,6 +1,18 @@\n"
                        + "1 import re\n"
                        + "2 import textwrap\n"
                        + "3 import os\n"
                        + "4 import json\n"
                        + "5 \n"
                        + "6 \n"
                        + "7 class CodeChunk:\n"
                        + "8     start_line: int\n"
                        + "9     end_line: int\n"
                        + "10     code: str\n"
                        + "11 \n"
                        + "12     def __init__(self, start_line, end_line, code):\n"
                        + "13         self.start_line = start_line\n"
                        + "14         self.end_line = end_line\n"
                        + "15         self.code = code\n"
                        + "16 \n"
                        + "17 \n"
                        + "18 # Format the git diff into a format that can be used by the GPT-3.5 API\n",
                    )
                ],
            },
        }
        self.file_names_fixture = [
            "app.py",
            "formatter.py",
        ]
        self.file_paths_fixture = {
            "app.py": "gitreview_gpt/app.py",
            "formatter.py": "gitreview_gpt/formatter.py",
        }

    def test_format_git_diff(self):
        (
            formatted,
            file_chunks,
            code_change_chunks,
            file_names,
            file_paths,
        ) = formatter.format_git_diff(self.git_diff)

        self.assertEqual(formatted, self.git_diff_formatted_fixture)
        self.assertEqual(file_chunks, self.file_chunks_fixture)
        self.assertEqual(file_names, self.file_names_fixture)
        self.assertEqual(file_paths, self.file_paths_fixture)
        self.assertEqual(
            code_change_chunks["app.py"][""][0].code,
            self.code_change_chunks_fixture["app.py"][""][0].code,
        )
        self.assertEqual(
            code_change_chunks["app.py"]["run():"][0].code,
            self.code_change_chunks_fixture["app.py"]["run():"][0].code,
        )
        self.assertEqual(
            code_change_chunks["app.py"]["run():"][1].code,
            self.code_change_chunks_fixture["app.py"]["run():"][1].code,
        )
        self.assertEqual(
            code_change_chunks["formatter.py"][""][0].code,
            self.code_change_chunks_fixture["formatter.py"][""][0].code,
        )
