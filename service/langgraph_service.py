import time
from collections import OrderedDict
from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from service.llm_service import LLMService
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

# Enable in-memory prompt completion caching to reduce duplicate LLM calls
set_llm_cache(InMemoryCache())

SYSTEM_PROMPT = """You are a strictly read-only database assistant. You cannot modify, delete, or alter any data.

Guidelines:
1. Lookups: Use `search_records(table, search_term)` to find people or entities by name/keyword in one step. Always verify that both first and last names match the request before presenting a profile; if ambiguous or multiple matches exist, ask for clarification.
2. Schema: Table names represent entity types (e.g. `employees`, `users`, `departments`, `projects`), never individual person names or values. Query obvious tables directly without redundant schema discovery.
3. Counting: Use `count_records_table` for row counts and `count_tables` for total tables.
4. Listing: Use `list_records` only for browsing records with specific summary `fields`. Never browse unfiltered records to find a single person.
5. Traversal: For reports/logs, find the parent ID with `search_records`, then query child tables with `list_records(table, field="<entity>_id", value=id)`.
6. Token Budget: Minimize token usage by ALWAYS specifying the minimal necessary columns in `fields` (e.g. ['id', 'name', 'status']). Limit searches and listings to `limit=3` to `5` rows unless the user explicitly requests more. Never fetch all fields.
7. Casual Chat & Output: Reply directly to greetings without tools. Present results in concise Markdown."""


# Defines the data passed between LangGraph nodes during a chat request
class MainState(TypedDict):
    question: Optional[str]
    answer: Optional[Any]
    token_usage: Optional[dict]
    tool_calls: Optional[list]


class LanggraphService:
    """Manages the LangGraph agent workflow and connects it to the MCP tool server."""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.__graph = None
        self.__mcp_client = None
        self.__mcp_url = settings.mcp_url
        self._llm_service = llm_service or LLMService()
        self._llm: Optional[BaseChatModel] = None
        self._cache = OrderedDict()
        self._cache_ttl = settings.cache_ttl_seconds
        self._cache_max_size = settings.cache_max_size

    def get_cached_response(self, query: str) -> Optional[dict]:
        """Returns cached response if available and not expired."""
        if self._cache_ttl <= 0:
            return None

        key = query.strip().lower()
        if key not in self._cache:
            return None

        item = self._cache[key]
        if time.time() - item["timestamp"] > self._cache_ttl:
            del self._cache[key]
            return None

        self._cache.move_to_end(key)
        return item["data"]

    def cache_response(self, query: str, data: dict):
        """Stores a completed response in the in-memory cache."""
        if self._cache_ttl <= 0:
            return

        key = query.strip().lower()
        cached_data = dict(data)
        if "token_usage" in cached_data and isinstance(cached_data["token_usage"], dict):
            cached_data["token_usage"] = {
                **cached_data["token_usage"],
                "cached": True,
            }

        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = {
            "timestamp": time.time(),
            "data": cached_data,
        }

        if len(self._cache) > self._cache_max_size:
            self._cache.popitem(last=False)

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = self._llm_service.get_chat_model()
        return self._llm

    async def initialize(self) -> MultiServerMCPClient:
        """Initializes the MCP client connection if not already created."""
        if self.__mcp_client is not None:
            return self.__mcp_client

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
            logger.error("[ERROR] Failed to initialize MCP client: %s", e)
            raise

    async def close(self):
        """Clean up resources on service shutdown."""
        self.__mcp_client = None

    async def ask_question(self, state: MainState):
        """Invokes the AI agent with database tools to generate a verified answer."""
        question = state.get("question")
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]
        tool_calls = []

        if self.__mcp_client is None:
            await self.initialize()

        # Discover tools dynamically from the MCP server and bind them to the LLM
        tools = await self.__mcp_client.get_tools()
        agent = create_agent(self.llm, tools)
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

        logger.info("[INFO] Token usage: %s", token_usage)
        logger.info("[INFO] Tool calls: %s", tool_calls)

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
