"""Tests against the real model and the live web. Slow and non-deterministic.

Run with `pytest -m integration`. They are skipped without a real HF token in `.env`.
"""
import os

import pytest
import requests

from agent import BasicAgent

RANDOM_QUESTION_URL = "https://agents-course-unit4-scoring.hf.space/random-question"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("HF_TOKEN", "").startswith("hf_")
        or os.getenv("HF_TOKEN") == "hf_your_token_here",
        reason="needs a real HF_TOKEN",
    ),
]


@pytest.fixture(scope="module")
def agent():
    return BasicAgent()


def ask(agent, question):
    answer = agent(question)
    print(f"\nQ: {question}\nA: {answer}")
    return answer


def test_reversed_text_question(agent):
    answer = ask(
        agent,
        '.rewsna eht sa "tfel" drow eht fo etisoppo eht etirw ,ecnetnes siht dnatsrednu uoy fI',
    )
    assert answer.strip().strip(".").lower() == "right"


def test_question_that_needs_web_search(agent):
    answer = ask(
        agent,
        "How many studio albums were published by Mercedes Sosa between 2000 and 2009 "
        "(included)? You can use the latest 2022 version of english wikipedia.",
    )
    assert "3" in answer


@pytest.mark.parametrize("draw", range(3))
def test_random_course_question(agent, draw):
    """No known answer here: run it and read the printed Q/A yourself. Nothing is submitted."""
    response = requests.get(RANDOM_QUESTION_URL, timeout=15)
    response.raise_for_status()
    item = response.json()
    if item.get("file_name"):
        print(f"\n(question comes with an attached file: {item['file_name']})")
    print(f"task_id: {item['task_id']}")
    answer = agent(item["question"], task_id=item["task_id"], file_name=item.get("file_name"))
    print(f"Q: {item['question']}\nA: {answer}")
    assert answer.strip()
