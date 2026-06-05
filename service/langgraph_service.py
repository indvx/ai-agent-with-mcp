from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage
from dotenv import load_dotenv
import os, sys

load_dotenv()


from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


class MainState(TypedDict):
    question: Optional[str]
    answer: Optional[Any]
    token_usage: Optional[dict]
    tool_calls: Optional[list]


llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"), temperature=0, verbose=True
)


class LanggraphService:
    def __init__(self):
        self.__graph = None
        self.__mcp_client = None
        self.__mcp_url = os.getenv("MCP_URL", "http://localhost:8001/mcp")

    async def initialize(self):
        self.__mcp_client = MultiServerMCPClient(
            {
                "db_operation": {
                    "transport": "streamable_http",
                    "url": self.__mcp_url,
                }
            }
        )
        return self.__mcp_client

    async def ask_question(self, state: MainState):
        messages = []
        tool_calls = []
        token_usage = {}

        question = state.get("question")
        messages.append(HumanMessage(content=question))
        tools = await self.__mcp_client.get_tools()
        agent = create_agent(llm, tools)
        result = await agent.ainvoke({"messages": messages})
        ai_response = result["messages"][-1].content

        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        if isinstance(result, dict) and "messages" in result:
            for message in result["messages"]:
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append(tool_call)

                if hasattr(message, "usage_metadata") and message.usage_metadata:
                    input_tokens += message.usage_metadata.get("input_tokens", 0)
                    output_tokens += message.usage_metadata.get("output_tokens", 0)
                    total_tokens += message.usage_metadata.get("total_tokens", 0)

        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }
        return {
            "answer": ai_response,
            "token_usage": token_usage,
            "tool_calls": tool_calls,
        }

    def build_pipeline(self):
        if self.__graph is not None:
            return self.__graph

        pipeline = StateGraph(MainState)
        pipeline.add_node("chat", self.ask_question)
        pipeline.add_edge(START, "chat")
        pipeline.add_edge("chat", END)

        self.__graph = pipeline.compile()
        return self.__graph
