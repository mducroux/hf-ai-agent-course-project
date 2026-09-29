from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from config import get_hf_token
from tools import fetch_webpage, read_attached_file, reverse_text, web_search

MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

tools = [web_search, fetch_webpage, read_attached_file, reverse_text]

SYSTEM_PROMPT = """You are a research assistant answering questions that have one short, factual answer.

- Use the web_search tool for any fact you are not certain about, and search again with a
  different query if the first results do not answer the question.
- Search snippets are partial. When you need details, counts or lists, open the best page with
  fetch_webpage (e.g. the Wikipedia article) and read it carefully before answering.
- If the question mentions an attached file, call read_attached_file with the task_id and file_name
  given in the message. For an image, pass the full question as `instruction`.
- If the question looks like backwards text (e.g. it starts with ".rewsna"), first call
  reverse_text with the ENTIRE question. The reversed result is the real question: answer that
  question, do not repeat or comment on the reversed text.
- Never reply that you need to search or look something up: call the tool instead.
- Your final reply is compared to a reference answer, so reply with the answer only: no
  explanation, no full sentence, no "FINAL ANSWER" prefix, no trailing period.
- Numbers as digits without units unless asked; names and words exactly as they should be written;
  lists comma-separated.
- If you cannot find the answer, give your best guess instead of refusing."""


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class BasicAgent:
    def __init__(self, chat=None):
        """`chat` lets tests inject a fake model; by default the real one is used."""
        if chat is None:
            llm = HuggingFaceEndpoint(
                repo_id=MODEL_ID, huggingfacehub_api_token=get_hf_token(), timeout=30
            )
            # Binding an empty tool list can be rejected by the API, so only bind real tools.
            chat = ChatHuggingFace(llm=llm)
            chat = chat.bind_tools(tools) if tools else chat
            # Network errors and timeouts happen; retry instead of failing the question.
            chat = chat.with_retry(stop_after_attempt=3)
        self.chat = chat

        builder = StateGraph(AgentState)
        builder.add_node("assistant", self._assistant)
        builder.add_node("tools", ToolNode(tools))

        builder.add_edge(START, "assistant")
        # Route to tools if the last message requests one, otherwise finish.
        builder.add_conditional_edges("assistant", tools_condition)
        builder.add_edge("tools", "assistant")
        self.graph = builder.compile()

    def _assistant(self, state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        return {"messages": [self.chat.invoke(messages)]}

    def __call__(self, question: str, task_id: str | None = None, file_name: str | None = None) -> str:
        content = question
        if file_name:
            content += (
                f"\n\n[Attached file: {file_name} (task_id: {task_id}). "
                "Use read_attached_file to read it.]"
            )
        result = self.graph.invoke({"messages": [HumanMessage(content=content)]})
        answer = result["messages"][-1].content
        return answer
