from unittest.mock import MagicMock

import pytest

import tools
from tools import fetch_webpage, reverse_text, web_search


@pytest.fixture
def fake_ddgs(monkeypatch):
    """Replace DDGS so tests don't hit the network."""
    client = MagicMock()
    monkeypatch.setattr(tools, "DDGS", lambda: client)
    return client


def test_web_search_formats_results(fake_ddgs):
    fake_ddgs.text.return_value = [
        {"title": "Title A", "href": "https://a.example", "body": "Snippet A"},
        {"title": "Title B", "href": "https://b.example", "body": "Snippet B"},
    ]

    output = web_search.invoke({"query": "anything"})

    assert "Title A" in output and "https://a.example" in output and "Snippet A" in output
    assert "Title B" in output
    fake_ddgs.text.assert_called_once_with("anything", max_results=5)


def test_web_search_returns_error_text_instead_of_raising(fake_ddgs):
    fake_ddgs.text.side_effect = RuntimeError("rate limited")
    output = web_search.invoke({"query": "anything"})
    assert output.startswith("Search failed:") and "rate limited" in output


@pytest.mark.integration
def test_web_search_live():
    output = web_search.invoke({"query": "Mercedes Sosa discography"})
    print(f"\n{output[:500]}")
    assert "Sosa" in output


def test_reverse_text_reads_backwards_text():
    assert reverse_text.invoke({"text": "tfel"}) == "left"


def test_fetch_webpage_returns_readable_text(monkeypatch):
    html = "<html><script>var x=1;</script><body><nav>menu</nav><h1>Title</h1><p>Hello world</p></body></html>"
    response = MagicMock(text=html, headers={"Content-Type": "text/html"})
    monkeypatch.setattr(tools.requests, "get", lambda *a, **k: response)

    output = fetch_webpage.invoke({"url": "https://example.com"})

    assert "Title" in output and "Hello world" in output
    assert "var x" not in output and "menu" not in output
