# gitreview-gpt

`gitreview-gpt` reviews your git changes with ChatGPT 3.5 from command line and provides detailed review comments with the corresponding line numbers.
Your `git diff` is extensively parsed to a well comprehensible format for the `gpt-3.5-turbo` model to get precise feedback based on your code changes.


![Screenshot 2023-07-17 at 13 40 00](https://github.com/fynnfluegge/gitreview-gpt/assets/16321871/5b8e4f1a-3401-4e9d-91c1-cce6683a6a80)

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

#### Create your personal OpenAI Api key and add it to your environment with:

```
export OPENAI_API_KEY=<YOUR_API_KEY>
```

#### Install with `pipx`:

```
pipx install git+https://github.com/fynnfluegge/gitreview-gpt.git
```
