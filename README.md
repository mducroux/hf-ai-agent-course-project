---
title: Final Assignment AI Agent Course
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

## The agent

`BasicAgent` is a LangGraph graph with two nodes. The `assistant` node calls the model with the system prompt and the conversation. If the model asks for a tool, the `tools` node runs it and the result goes back to the assistant. The loop ends when the model replies without a tool call, and that reply is the submitted answer.

- **Model:** `meta-llama/Llama-3.3-70B-Instruct` through Hugging Face inference (`CHAT_MODEL` in `models.py`).
- **Tools** (`tools.py`):
  - `web_search`: DuckDuckGo, top 5 results.
  - `fetch_webpage`: downloads a page and returns its text (first 15,000 characters), for when snippets are not enough.
  - `read_attached_file`: reads the file attached to a question. Text, code and CSV files are returned as text, Excel sheets as CSV, images are described by a vision model (`Qwen2.5-VL-72B-Instruct`, given the question so it knows what to look for), and audio is transcribed with `whisper-large-v3`.
  - `reverse_text`: reads backwards text.
- **Attached files:** several course questions come with a file, which the agent needs at run time, on the Space as well as locally.
- **Known limits:**
  - No tool can watch videos (e.g. the YouTube bird-species question).
  - Attachments other than text, code, CSV, Excel, images and audio (for example PDF, Word, PowerPoint) are reported as unsupported.
  - Python attachments are read, not run, so the output of longer scripts can be wrong.
  - Image answers depend on the vision model (e.g. reading a chess position); audio transcription has not been checked on the real course recordings.
  - Attachments need GAIA access (see above); without it those questions fail.
  - `fetch_webpage` keeps only the first 15,000 characters of a page, so information further down can be missed. `web_search` (DuckDuckGo) can be rate limited.

## Local setup

```bash
git clone https://huggingface.co/spaces/mducroux/Final_Assignment_AI_Agent_Course
cd Final_Assignment_AI_Agent_Course          # your clone's folder

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Create a token at https://huggingface.co/settings/tokens and put it in a `.env` file (loaded automatically by `agent.py`):

```bash
cp .env.example .env      # then replace the placeholder with your real token
```

Variables already set in your environment take priority over `.env`. On the Space, set `HF_TOKEN` as a secret in the Space settings.

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
pytest -m integration -k random   # the agent on 3 random course questions (nothing submitted)
```
