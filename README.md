---
title: Template Final Assignment
emoji: 🕵🏻‍♂️
colorFrom: indigo
colorTo: indigo
sdk: gradio
sdk_version: 5.25.2
app_file: app.py
pinned: false
hf_oauth: true
# optional, default duration is 8 hours/480 minutes. Max duration is 30 days/43200 minutes.
hf_oauth_expiration_minutes: 480
---

# Final Assignment: AI Agents Course

Gradio app that fetches the course questions, runs an agent on them, submits the answers to the scoring API and shows the score.

Space configuration reference: https://huggingface.co/docs/hub/spaces-config-reference

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` | Gradio UI: login, fetch questions, run the agent, submit answers |
| `agent.py` | The agent (`BasicAgent`): a LangGraph loop of model and tools, plus the system prompt |
| `tools.py` | Tools the agent can call: `web_search`, `fetch_webpage`, `read_attached_file`, `reverse_text` |
| `attachments.py` | Downloads the files attached to questions (scoring API, then GAIA dataset) |
| `readers.py` | Turns a local file into text, by file type (text, Excel, images, audio) |
| `models.py` | Hugging Face vision and speech-to-text calls, used by `readers.py` |
| `config.py` | Loads `.env` and provides the Hugging Face token |
| `tests/test_agent.py` | Fast tests of the agent with a scripted fake model |
| `tests/test_tools.py` | Fast tests of the tools, plus one live search |
| `tests/test_attachments.py` | Fast tests of attachment downloading |
| `tests/test_readers.py` | Fast tests of file reading |
| `tests/test_agent_live.py` | Slow tests with the real model and live web |
| `pytest.ini` | pytest settings (test path, `integration` marker, output not captured) |
| `requirements.txt` | Runtime dependencies (installed by the Space) |
| `requirements-dev.txt` | Development dependencies (`pytest`) |
| `.env.example` | Template for your local `.env` |
| `.gitignore` | Ignores venvs, caches, `.env` files, editor files |

## The agent

`BasicAgent` is a LangGraph graph with two nodes. The `assistant` node calls the model with the system prompt and the conversation. If the model asks for a tool, the `tools` node runs it and the result goes back to the assistant. The loop ends when the model replies without a tool call, and that reply is the submitted answer.

- **Model:** `meta-llama/Llama-3.3-70B-Instruct` through Hugging Face inference (`MODEL_ID` in `agent.py`). The previous `Qwen2.5-Coder-32B-Instruct` was rejected by the API because it does not support tool calling on the provider that serves it.
- **Reliability:** requests time out after 30 seconds and are retried up to 3 times.
- **Tools** (`tools.py`):
  - `web_search`: DuckDuckGo, top 5 results.
  - `fetch_webpage`: downloads a page and returns its text (first 15,000 characters), for when snippets are not enough.
  - `read_attached_file`: reads the file attached to a question. Text, code and CSV files are returned as text, Excel sheets as CSV, images are described by a vision model (`Qwen2.5-VL-72B-Instruct`, given the question so it knows what to look for), and audio is transcribed with `whisper-large-v3`.
  - `reverse_text`: reads backwards text.
- **System prompt** (`SYSTEM_PROMPT` in `agent.py`): tells the model to use the tools, to reverse backwards questions, and to reply with the bare answer only, because answers are compared to a reference answer.
- **Attached files:** the scoring API's `/files/{task_id}` currently returns 404, so `attachments.py` falls back to the [GAIA dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA), where the same files live. It is gated: accept its terms on the account that owns your token, or attachments cannot be read. Python files are read, not executed, so the agent has to work out their output itself.
- **Known limits:** no tool can watch videos, and files other than text, Excel, images and audio are not supported. Answers are not fully deterministic, so the same question can get different answers on different runs.

## Local setup

```bash
git clone https://huggingface.co/spaces/mducroux/Final_Assignment_Template
cd Final_Assignment_Template          # your clone's folder

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Create a token at https://huggingface.co/settings/tokens and put it in a `.env` file (git-ignored, loaded automatically by `agent.py`):

```bash
cp .env.example .env      # then replace the placeholder with your real token
```

Variables already set in your environment take priority over `.env`. On the Space, set `HF_TOKEN` as a secret in the Space settings.

`.venv` starts with a dot, so it is hidden by default (`ls -a`, or `Ctrl+H` in a file manager). In PyCharm, select `.venv/bin/python` under Settings > Project > Python Interpreter.

Note: `hf download ... --repo-type=space` is **not** a git clone. It only copies files into the Hugging Face cache, with no `.git` and no way to push. Use `git clone` to get a working copy.

## Running the app

```bash
hf auth login        # needed for the mocked login button (or rely on HF_TOKEN)
python app.py        # http://127.0.0.1:7860
```

`gradio[oauth]` is required by `gr.LoginButton`. Locally Gradio mocks the login with your Hugging Face token.

The "Run Evaluation & Submit All Answers" button runs the agent on **all** questions and submits the answers to the scoring API under your username. Don't use it for quick experiments; use the tests below.

## Testing the agent

Tests call the agent directly, with no Gradio and no submission. They come in two kinds:

```bash
pytest                    # fast: scripted fake model, no network, no token (under a second)
pytest -m integration     # slow: real model and live web, needs a real HF_TOKEN in .env
```

- **Fast tests** check our own code: that the model's answer is returned, that the system prompt is sent first, that a tool call runs and its result goes back to the model, and that the tools format their output and handle errors.
- **Integration tests** check answer quality against questions with known answers (the reversed-text question and the Mercedes Sosa question). They print `Q:` and `A:`. They are skipped when no real token is set and can fail intermittently, because the model and the web are not deterministic.

`-s` is set in `pytest.ini`, so print output shows on every run. Remove it from `addopts` if that gets too noisy.
