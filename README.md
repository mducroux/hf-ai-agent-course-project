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
| `agent.py` | The agent (`BasicAgent`). Build your own logic here |
| `tests/test_agent.py` | pytest tests for the agent |
| `pytest.ini` | pytest settings (test path, `integration` marker, output not captured) |
| `requirements.txt` | Runtime dependencies (installed by the Space) |
| `requirements-dev.txt` | Development dependencies (`pytest`) |
| `.gitignore` | Ignores venvs, caches, `.env` files, editor files |

## Local setup

```bash
git clone https://huggingface.co/spaces/mducroux/Final_Assignment_Template
cd Final_Assignment_Template          # your clone's folder

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

`.venv` starts with a dot, so it is hidden by default (`ls -a`, or `Ctrl+H` in a file manager). In PyCharm, select `.venv/bin/python` under Settings > Project > Python Interpreter.

Note: `hf download ... --repo-type=space` is **not** a git clone. It only copies files into the Hugging Face cache, with no `.git` and no way to push. Use `git clone` to get a working copy.

## Running the app

```bash
hf auth login        # or set HF_TOKEN; needed for the mocked login button
python app.py        # http://127.0.0.1:7860
```

`gradio[oauth]` is required by `gr.LoginButton`. Locally Gradio mocks the login with your Hugging Face token.

The "Run Evaluation & Submit All Answers" button runs the agent on **all** questions and submits the answers to the scoring API under your username. Don't use it for quick experiments; use the tests below.

## Testing the agent

Tests call the agent directly, with no Gradio and no submission.

```bash
pytest                    # fast offline tests
pytest -m integration     # also runs the agent on 3 live questions (fetch only, nothing submitted)
```

Each test prints `Q:` and `A:` so you can see what the agent answers (`-s` is set in `pytest.ini`, so the agent's own `print()` output shows too). Remove `-s` from `addopts` if this gets too noisy.

The current tests only check that the answer is a non-empty string. Once the agent does real work, add cases with a known question and expected answer.
