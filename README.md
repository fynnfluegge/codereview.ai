# gitreview-gpt

`gitreview-gpt` reviews your git changes with OpenAI's GPT-3.5 model from command line and provides detailed review comments with the corresponding line numbers.
Your `git diff` is extensively parsed to a well comprehensible format for the `gpt-3.5-turbo` completion api to get precise feedback based on your code changes.

![ezgif-5-956a1609ab](https://github.com/fynnfluegge/gitreview-gpt/assets/16321871/ce68fb34-2748-4929-aaaa-b2a1271301a5)

## ✨ Features

- **Get feedback and suggestions with the corresponding line numbers to your changes**
- **Review all changes in your workiung directory**
- **Review your staged changes only**
- **Review all your committed changes against the main branch**
- **Review your changed files all at once or separately**
- **Create a commit message for your changes**

## 🚀 Usage

- `rgpt review`: Reviews all changes in your working directory.
- `rgpt review --staged`: Reviews all staged changes in your working directory.
- `rgpt review --target <BRANCH_NAME>`: Reviews all committed changes in your current branch compared to `<BRANCH_NAME>`.
- `rgpt commit`: Creates a commit message for your staged changes.

## 📋 Requirements

- Python >= 3.11

## 🔧 Installation

Create your personal OpenAI Api key and add it as `$OPENAI_API_KEY` to your environment with:

```
export OPENAI_API_KEY=<YOUR_API_KEY>
```

Install with `pipx`:

```
pipx install git+https://github.com/fynnfluegge/gitreview-gpt.git
```
