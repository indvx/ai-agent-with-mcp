from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
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
        messages = []
        tool_calls = []

        question = state.get("question")
        messages.append(HumanMessage(content=question))
        messages.append(
            SystemMessage(
                content="""You are an MCP database assistant. Answer database questions ONLY using data retrieved through MCP tools.
                    Rules:
                        - Casual messages (hi, hello, thanks, etc.) → respond normally; don't use database tools.
                        - For database questions, ALWAYS retrieve the actual data before answering.
                        - Never assume or invent tables, fields, records, or values.
                        - Unknown table → `get_tables`, then CONTINUE to the data query.
                        - Unknown fields → `get_fields`, then CONTINUE to the data query.
                        - `get_tables`/`get_fields` are discovery steps, NOT final answers.
                        - Use `filter` or the appropriate query tool to retrieve data.
                        - Only use tables/fields confirmed by successful tool results.
                        - `success=false` → don't use the result; explain the error and try a valid alternative.
                        - Empty results → verify the table, field, and filter before concluding.
                        - Employee information is in `employees`; verify required fields before querying.
                        - Never answer database questions from model knowledge or assumptions.
                        - If data cannot be verified, say so.
                        - If the request is ambiguous, ask for clarification.
                        - Respond in Markdown with relevant emojis.

                    Before answering, verify:
                    1. Correct table
                    2. Correct fields
                    3. Successful query
                    4. Returned data matches the question
                    5. No invented information
                """
            )
        )

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

        print("token_usage", token_usage, file=sys.stderr)
        print("tool_calls", tool_calls, file=sys.stderr)

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
