from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os, sys

load_dotenv()

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from service.llm_service import LLMService


# Defines the data passed between LangGraph nodes during a chat request
class MainState(TypedDict):
    question: Optional[str]
    answer: Optional[Any]
    token_usage: Optional[dict]
    tool_calls: Optional[list]


# Shared chat model instance for the AI agent
llm = LLMService().get_chat_model()


class LanggraphService:
    """Manages the LangGraph agent workflow and connects it to the MCP tool server."""

    def __init__(self):
        self.__graph = None
        self.__mcp_client = None
        self.__mcp_url = os.getenv("MCP_URL", "http://localhost:8001/mcp")

    async def initialize(self):
        """Connects to the FastMCP database tool server running over HTTP streaming."""
        try:
            self.__mcp_client = MultiServerMCPClient(
                {
                    "db_operation": {
                        "transport": "streamable_http",
                        "url": self.__mcp_url,
                    }
                }
            )
            return self.__mcp_client
        except Exception as e:
            print(f"Error initializing MCP client: {e}", file=sys.stderr)
            raise e

    async def ask_question(self, state: MainState):
        """Invokes the AI agent with database tools to generate a verified answer."""
        messages = []
        tool_calls = []

        question = state.get("question")
        messages.append(HumanMessage(content=question))
        messages.append(
            SystemMessage(
                content="""You are an intelligent, generic MCP database assistant. You can dynamically inspect, query, and reason about ANY relational database schema without hardcoded assumptions.

                    Universal Database Workflow:
                        1. Schema & Table Discovery:
                           - When an entity or topic is asked about, find relevant tables using `get_table_names(search=...)` or list tables using `get_table_names()`.
                           - Use `get_fields(table=...)` to inspect column names, types, and primary/foreign keys before querying unfamiliar tables.
                           - To count total tables in the database, use `count_tables`.
                        2. Relational Traversal (Multi-Table Queries & Reports):
                           - When asked for a report, profile, log, or summary of a specific entity (e.g. employee daily report, customer orders, user activity):
                             a. Locate the parent entity in its primary table to obtain its identifier (e.g. `id` or code).
                             b. Identify related child tables via naming conventions or foreign keys (e.g. `<entity_singular>_id` such as `employee_id`, `customer_id`, `user_id`).
                             c. Query the child tables with `list_records(table=..., field="<foreign_key>", value=<id>, desc=True)`.
                             d. Combine and synthesize data from the parent and child tables into a clean, unified response.
                        3. Counting vs. Listing Records:
                           - To count total records, rows, or matching items in a table (e.g. 'how many records', 'total count', 'how many users'), ALWAYS use `count_records_table`. NEVER use `list_records` to count items.
                           - Use `list_records` only when you need to view or display the actual record data.
                        4. Query & Token Optimization:
                           - Casual messages (hi, hello, etc.) → respond naturally without database tools.
                           - When querying wide tables, specify only the relevant summary `fields` (e.g. `fields=['id', 'name', 'status', ...]`) to prevent context token overflow.
                           - For general listing requests, fetch a single page (limit=10 to 15). Summarize returned items and state the total count or offer to fetch more. Do NOT fetch multiple pages in a single turn.
                           - For boolean/tinyint status columns, 1 represents active/true and 0 represents inactive/false.
                        5. Presentation & Formatting:
                           - When presenting daily reports or multi-point updates:
                             * Cleanly format project/task headings and bullet points (convert any HTML formatting into clean Markdown).
                             * Clearly display timing, durations, working hours, and summary metrics.
                           - Respond concisely in clean, human-readable Markdown with relevant emojis.
                           - Never assume, hallucinate, or invent tables, fields, records, or values.
                """
            )
        )

        # Discover tools dynamically from the MCP server and bind them to the LLM
        tools = await self.__mcp_client.get_tools()
        agent = create_agent(llm, tools)
        result = await agent.ainvoke({"messages": messages})
        ai_response = result["messages"][-1].content
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        # Sum token usage across all internal tool-calling turns
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

        print("token_usage", token_usage, file=sys.stderr)
        print("tool_calls", tool_calls, file=sys.stderr)

        return {
            "answer": ai_response,
            "token_usage": token_usage,
            "tool_calls": tool_calls,
        }

    def build_pipeline(self):
        """Compiles the single-node LangGraph execution graph for chat requests."""
        if self.__graph is not None:
            return self.__graph

        pipeline = StateGraph(MainState)
        pipeline.add_node("chat", self.ask_question)
        pipeline.add_edge(START, "chat")
        pipeline.add_edge("chat", END)

        self.__graph = pipeline.compile()
        return self.__graph
