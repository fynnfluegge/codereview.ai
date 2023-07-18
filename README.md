# gitreview-gpt

`gitreview-gpt` reviews your git changes with OpenAI's GPT-3.5 model from command line and provides detailed review comments with the corresponding line numbers.
Your `git diff` is extensively parsed to a well comprehensible format for the `gpt-3.5-turbo` completion api to get precise feedback based on your code changes.


![ezgif-5-cf7e3d5d47](https://github.com/fynnfluegge/gitreview-gpt/assets/16321871/80852b6a-020e-45aa-88d7-edc5544cac26)


## ✨ Features

- **Review all your committed changes against the main branch**
- **Review your staged changes only**
- **Review your changed files all at once or separately**
- **Create a commit message for your changes**

## 🚀 Usage

- `rgpt review`: Reviews all your changes against the `main` branch
- `rgpt review --staged`: Reviews all your staged changes
- `rgpt commit`: Creates a commit message for your staged changes

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
