import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web with DuckDuckGo and return the top results (title, URL, snippet).

    Use it for facts you don't know or that may have changed. Phrase the query
    like a search-engine query, not a full question.
    """
    try:
        results = DDGS().text(query, max_results=5)
    except Exception as e:
        return f"Search failed: {e}"
    if not results:
        return "No results found."
    return "\n\n".join(f"{r['title']}\n{r['href']}\n{r['body']}" for r in results)


@tool
def reverse_text(text: str) -> str:
    """Reverse a string character by character. Use it to read text that is written backwards."""
    return text[::-1]


MAX_PAGE_CHARS = 15_000


@tool
def fetch_webpage(url: str) -> str:
    """Download a web page and return its readable text (truncated if long).

    Use it after web_search to read a full page, e.g. a Wikipedia article, when the
    search snippets are not enough to answer.
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Could not fetch {url}: {e}"
    if "html" not in response.headers.get("Content-Type", "html"):
        return f"Cannot read {url}: unsupported content type {response.headers['Content-Type']}."

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = "\n".join(line for line in soup.get_text("\n", strip=True).splitlines() if line)
    if len(text) > MAX_PAGE_CHARS:
        text = text[:MAX_PAGE_CHARS] + f"\n[truncated: page has {len(text)} characters]"
    return text
