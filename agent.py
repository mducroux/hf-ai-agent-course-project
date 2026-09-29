import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

MODEL_ID = "Qwen/Qwen2.5-Coder-32B-Instruct"

tools = []


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def _get_token() -> str:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise RuntimeError(
            "No Hugging Face token found. Set HF_TOKEN (or HUGGINGFACEHUB_API_TOKEN)."
        )
    return token


class BasicAgent:
    def __init__(self):
        llm = HuggingFaceEndpoint(repo_id=MODEL_ID, huggingfacehub_api_token=_get_token())
        chat = ChatHuggingFace(llm=llm)
        # Binding an empty tool list can be rejected by the API, so only bind real tools.
        self.chat = chat.bind_tools(tools) if tools else chat

        builder = StateGraph(AgentState)
        builder.add_node("assistant", self._assistant)
        builder.add_node("tools", ToolNode(tools))

        builder.add_edge(START, "assistant")
        # Route to tools if the last message requests one, otherwise finish.
        builder.add_conditional_edges("assistant", tools_condition)
        builder.add_edge("tools", "assistant")
        self.graph = builder.compile()

    def _assistant(self, state: AgentState):
        return {"messages": [self.chat.invoke(state["messages"])]}

    def __call__(self, question: str) -> str:
        print(f"Agent received question (first 50 chars): {question[:50]}...")
        result = self.graph.invoke({"messages": [HumanMessage(content=question)]})
        answer = result["messages"][-1].content
        print(f"Agent returning answer: {answer}")
        return answer
