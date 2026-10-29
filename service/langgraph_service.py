from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os, sys

load_dotenv()


from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


# Defines the data passed between LangGraph nodes during a chat request
class MainState(TypedDict):
    question: Optional[str]
    answer: Optional[Any]
    token_usage: Optional[dict]
    tool_calls: Optional[list]


# Shared OpenAI chat model instance for the AI agent
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"), temperature=0, verbose=True
)


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
                content="""You are an MCP database assistant. Answer database questions using data retrieved through MCP tools.

                    Common Tables & Key Columns:
                        - `employees`: id, code, first_name, last_name, email, role, job_role, department_id, status
                        - `users`: id, full_name, email, is_active, is_verified
                        - `departments`: id, name
                        - `activities`: id, employee_id, activity_type, in_time, out_time, status (stores employee activity records; link via `employee_id`)
                        - `reports`: id, employee_id, report, start_time, end_time, total_working_hours (stores employee work/daily reports; link via `employee_id`)
                        - For other tables, discover them using `get_table_names` and `get_fields`.

                    Query & Token Optimization Rules:
                        - Casual messages (hi, hello, etc.) → respond naturally without database tools.
                        - When querying wide tables (especially `employees`), ALWAYS specify only the relevant summary `fields` (e.g. `fields=['id', 'first_name', 'last_name', 'email', 'job_role', 'status']`) to prevent context token overflow.
                        - For general listing requests, fetch a single page (limit=10 to 15). Summarize the returned items and state the total count or offer to fetch more. Do NOT fetch multiple pages in a single turn.
                        - For boolean/tinyint status columns (e.g. `status` in `employees`), 1 represents active/true and 0 represents inactive/false.
                        - Never assume or invent tables, fields, records, or values.
                        - Only use tables and fields confirmed by tool results.
                        - Respond concisely in clean, human-readable Markdown with relevant emojis.
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
