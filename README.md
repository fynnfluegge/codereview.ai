<div align="center">

# Let your code get reviewd by AI

[![Build](https://github.com/fynnfluegge/gitreview-gpt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/fynnfluegge/gitreview-gpt/actions/workflows/build.yml)
[![Publish](https://github.com/fynnfluegge/gitreview-gpt/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/fynnfluegge/gitreview-gpt/actions/workflows/publish.yml)
<a href="https://github.com/fynnfluegge/rocketnotes/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-green.svg"/>
</a>
  
</div>

`gitreview-gpt` reviews your git changes with OpenAI's GPT-3.5 model from command line and provides detailed review comments with the corresponding line numbers.
Your `git diff` is extensively parsed to a well comprehensible format for the `gpt-3.5-turbo` completion api to get precise feedback based on your code changes.

![ezgif-5-956a1609ab](https://github.com/fynnfluegge/gitreview-gpt/assets/16321871/ce68fb34-2748-4929-aaaa-b2a1271301a5)

## ✨ Features

- **Get feedback and suggestions with the corresponding line numbers to git changes**
- **Reviews all changes in the working directory**
- **Reviews only staged changes**
- **Reviews all committed changes against a specific branch**
- **Reviews all modified files at once or separately**
- **Creates a commit message for your changes**

## 🚀 Usage

- `rgpt review`: Reviews all changes in your working directory.
- `rgpt review --staged`: Reviews all staged changes in your working directory.
- `rgpt review --target $BRANCH`: Reviews all committed changes in your current branch compared to `$BRANCH`.
- `rgpt commit`: Creates a commit message for your staged changes.

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
> It is recommended to use `pipx` for installation, nonetheless it is also possible to use `pip`
