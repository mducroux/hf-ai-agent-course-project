import pytest
import requests

from agent import BasicAgent

QUESTIONS_URL = "https://agents-course-unit4-scoring.hf.space/questions"


@pytest.fixture
def agent():
    return BasicAgent()


@pytest.mark.parametrize(
    "question",
    [
        "What is 2 + 2?",
        "",
        "Unicode question: où est la bibliothèque ? 你好",
        "x" * 10_000,
    ],
)
def test_agent_returns_non_empty_string(agent, question):
    answer = agent(question)
    print(f"\nQ: {question[:100]}\nA: {answer}")
    assert isinstance(answer, str)
    assert answer.strip()


@pytest.mark.integration
def test_agent_answers_real_questions(agent):
    """Runs the agent on a few live questions. Not submitted or scored."""
    response = requests.get(QUESTIONS_URL, timeout=15)
    response.raise_for_status()
    questions = response.json()[:3]

    assert questions
    for item in questions:
        answer = agent(item["question"])
        print(f"\nQ: {item['question']}\nA: {answer}")
        assert isinstance(answer, str) and answer.strip()
