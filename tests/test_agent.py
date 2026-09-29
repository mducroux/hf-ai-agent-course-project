"""Fast, deterministic tests: the model is replaced by a scripted fake."""
import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

import agent as agent_module
import tools
from agent import BasicAgent


class ScriptedChat:
    """Stands in for the chat model: returns the given replies in order and records its inputs."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(list(messages))
        return self.replies.pop(0)


def tool_call(query, call_id="call_1"):
    return AIMessage(
        content="", tool_calls=[{"name": "web_search", "args": {"query": query}, "id": call_id}]
    )


@pytest.fixture
def fake_search(monkeypatch):
    """Make web_search return a fixed result without touching the network."""
    monkeypatch.setattr(tools, "DDGS", lambda: _FakeDDGS())


class _FakeDDGS:
    def text(self, query, max_results):
        return [{"title": "Fake title", "href": "https://fake.example", "body": "The answer is 42."}]


def test_returns_the_models_answer():
    agent = BasicAgent(chat=ScriptedChat(AIMessage(content="Paris")))
    assert agent("What is the capital of France?") == "Paris"



def test_system_prompt_is_sent_first():
    chat = ScriptedChat(AIMessage(content="ok"))
    BasicAgent(chat=chat)("Q?")

    first, second = chat.calls[0]
    assert isinstance(first, SystemMessage) and first.content == agent_module.SYSTEM_PROMPT
    assert isinstance(second, HumanMessage) and second.content == "Q?"


def test_attached_file_is_announced_to_the_model():
    chat = ScriptedChat(AIMessage(content="ok"))
    BasicAgent(chat=chat)("Q?", task_id="abc", file_name="abc.png")

    question = chat.calls[0][-1].content
    assert "abc.png" in question and "task_id: abc" in question


def test_tool_call_is_executed_and_result_goes_back_to_the_model(fake_search):
    chat = ScriptedChat(tool_call("meaning of life"), AIMessage(content="42"))

    answer = BasicAgent(chat=chat)("What is the answer?")

    assert answer == "42"
    assert len(chat.calls) == 2  # ask -> (tool runs) -> ask again
    tool_message = chat.calls[1][-1]
    assert isinstance(tool_message, ToolMessage)
    assert "The answer is 42." in tool_message.content


def test_missing_token_gives_a_clear_error(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HF_TOKEN"):
        BasicAgent()
