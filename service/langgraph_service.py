import asyncio
import logging
import os
from typing import Any, Optional, TypedDict

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, START, StateGraph

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a database assistant using MCP tools.
For database questions, use tool results; never invent tables, columns, or records.
Use only schema details confirmed by successful tool results. Discover tables or
columns when needed, then continue to retrieve the requested data. Check tool
success and verify results before answering. If results are empty, validate the
table, fields, and filters before concluding. Ask for clarification when needed.
Return a concise, relevant answer in Markdown. Do not expose sensitive fields."""


class MainState(TypedDict):
    question: Optional[str]
    answer: Optional[Any]
    token_usage: Optional[dict]
    tool_calls: Optional[list]


llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    temperature=0,
)


class LanggraphService:
    def __init__(self):
        self.__graph = None
        self.__mcp_client = None
        self.__tools = None
        self.__agent = None
        self.__mcp_url = os.getenv("MCP_URL", "http://localhost:8001/mcp")
        self.__initialize_lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the MCP client and agent once per service instance."""
        if self.__agent is not None:
            return self.__mcp_client

        async with self.__initialize_lock:
            if self.__agent is not None:
                return self.__mcp_client

            try:
                client = MultiServerMCPClient(
                    {
                        "db_operation": {
                            "transport": "streamable_http",
                            "url": self.__mcp_url,
                        }
                    }
                )
                tools = await client.get_tools()
                agent = create_agent(llm, tools)

                self.__mcp_client = client
                self.__tools = tools
                self.__agent = agent
                logger.info("MCP agent initialized with %d tools", len(tools))
                return self.__mcp_client
            except Exception:
                logger.exception("Error initializing MCP client and agent")
                raise

    async def ask_question(self, state: MainState):
        await self.initialize()
        question = state.get("question") or ""

        # Keep the static system instructions first to preserve a stable prompt prefix.
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]

        result = await self.__agent.ainvoke({"messages": messages})
        result_messages = result.get("messages", [])
        ai_response = result_messages[-1].content if result_messages else ""

        tool_calls = []
        model_calls = []
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        for message in result_messages:
            message_tool_calls = getattr(message, "tool_calls", None)
            if message_tool_calls:
                tool_calls.extend(message_tool_calls)

            usage = getattr(message, "usage_metadata", None)
            if not usage:
                continue

            call_usage = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
            model_calls.append(call_usage)
            input_tokens += call_usage["input_tokens"]
            output_tokens += call_usage["output_tokens"]
            total_tokens += call_usage["total_tokens"]

        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "model_calls": model_calls,
            "model_call_count": len(model_calls),
        }

        logger.info("Token usage for request: %s", token_usage)
        logger.info("MCP tool call count: %d", len(tool_calls))

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
