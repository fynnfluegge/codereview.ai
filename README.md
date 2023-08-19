<div align="center">

# Let your code changes get reviewed by AI with codereview-agi

[![Build](https://github.com/fynnfluegge/gitreview-gpt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/fynnfluegge/gitreview-gpt/actions/workflows/build.yml)
[![Publish](https://github.com/fynnfluegge/codereview-agi/actions/workflows/publish.yml/badge.svg?event=release)](https://github.com/fynnfluegge/codereview-agi/actions/workflows/publish.yml)
<img src="https://img.shields.io/badge/License-MIT-green.svg"/>
</a>
  
</div>

<div align="center">
  
![ezgif-5-956a1609ab](https://github.com/fynnfluegge/gitreview-gpt/assets/16321871/ce68fb34-2748-4929-aaaa-b2a1271301a5)

</div>

Get review suggestions to changes in your git working directory or to any committed changes in your current branch against a target branch and let these suggestions get applied to your code
with an informative commit message.

## ✨ Features

- **Get feedback and suggestions with the corresponding line numbers to your git changes in your terminal**
- **Let your current working directory get reviewed (staged and unstaged changes)**
- **Let all commits of your current branch get reviewed against any specific target branch**
- **Let AI-generated review suggestions get applied to your code**
- **Let a commit message get generated for your current changes**

> [!NOTE]
> Review suggestions will only be applied to files without unstaged changes, so that nothing is overridden.

## 🚀 Usage

- `rgpt review`: Reviews all changes in your working directory and applies review suggestions to related files autonomously.
- `rgpt review --readonly`: Reviews all changes without applying the suggestions to the code.
- `rgpt review --guided`: User needs to confirm review process for each file. Useful if not all files should get reviewed.
- `rgpt review --target $BRANCH`: Reviews all committed changes in your current branch compared to `$BRANCH`.
- `rgpt review --gpt4`: Use GPT-4 model (default is GPT-3.5).
- `rgpt commit`: Generates a commit message for your staged changes.

## 📋 Requirements

- Python >= 3.8

## 🔧 Installation

Create your personal OpenAI Api key and add it as `$OPENAI_API_KEY` to your environment with:

```
export OPENAI_API_KEY=<YOUR_API_KEY>
```

Install with `pipx`:

```
pipx install gitreview-gpt
```

> [!NOTE]
> It is recommended to use `pipx` for installation, nonetheless it is also possible to use `pip`.
