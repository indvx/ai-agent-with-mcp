import re
import time
from collections import OrderedDict
from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from database import SessionLocal
from sql.crud.chat import get_recent_messages, save_message, get_or_create_session
from sql.models.chat_session import ChatSession
from service.llm_service import LLMService
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

CASUAL_PATTERNS = [
    r"^(hi|hello|hey|greetings|howdy)\b",
    r"^how are you\b",
    r"^who (are you|am i)\b",
    r"^what is your name\b",
    r"^what can you do\b",
    r"^(thanks|thank you|thx)\b",
    r"^(bye|goodbye|see you)\b",
    r"^(good morning|good afternoon|good evening|good night)\b",
]

DB_PATTERNS = [
    r"\b(table|tables|schema|database|db|column|columns)\b",
    r"\b(count|list|search|find|show|records?|rows?)\b",
    r"\b(employee|employees|user|users|department|departments)\b",
]

CASUAL_SYSTEM_PROMPT = """You are a helpful and polite database assistant.
For greetings, pleasantries, questions about who you are or what you can do, answer conversationally, politely, and concisely.
If the user asks questions unrelated to database capabilities, answer concisely and remind them you can help query and analyze their database."""

INTENT_PROMPT = """You are a query intent classifier. Classify the user query into either "casual" or "database".

- "casual": greetings, pleasantries, small talk, identity questions ("who are you", "who am i"), or general capability questions.
- "database": queries asking about data, tables, records, schemas, counts, lists, employees, users, departments, or database searches.

Query: "{query}"

Respond with only one word: either "casual" or "database"."""

SYSTEM_PROMPT = """You are a strictly read-only database assistant. You cannot modify, delete, or alter any data.

Guidelines:
1. Lookups: Use `search_records(table, search_term)` to find people or entities by name/keyword in one step. Always verify that both first and last names match the request before presenting a profile; if ambiguous or multiple matches exist, ask for clarification.
2. Schema: Table names represent entity types (e.g. `employees`, `users`, `departments`, `projects`), never individual person names or values. Query obvious tables directly without redundant schema discovery.
3. Counting: Use `count_records_table` for row counts and `count_tables` for total tables.
4. Listing: Use `list_records` only for browsing records with specific summary `fields`. Never browse unfiltered records to find a single person.
5. Traversal: For reports/logs, find the parent ID with `search_records`, then query child tables with `list_records(table, field="<entity>_id", value=id)`.
6. Token Budget: Minimize token usage by ALWAYS specifying the minimal necessary columns in `fields` (e.g. ['id', 'name', 'status']). Limit searches and listings to `limit=3` to `5` rows unless the user explicitly requests more. Never fetch all fields.
7. Casual Chat & Output: Reply directly to greetings without tools. Present results in concise Markdown.
8. Context & Follow-ups: When prior conversation turns exist in history, refer to them directly. Do NOT re-execute tools if the information is already provided in previous turns."""

CHAT_SESSION_PROMPT = """You are a session title generator. Analyze the user's query and generate a short, meaningful title that represents the main topic of the conversation.

Query: "{query}"

Rules:
- Generate a title of 3–6 words.
- Keep it simple, clear, and relevant.
- Do not copy the entire user query.
- Generate the title only once per session.
- Do not generate titles for subsequent messages.
- Return only the title without any explanation.
"""

# Defines the data passed between LangGraph nodes during a chat request
class MainState(TypedDict):
    question: Optional[str]
    session_id: Optional[str]
    answer: Optional[Any]
    token_usage: Optional[dict]
    tool_calls: Optional[list]
    intent: Optional[str]


class LanggraphService:
    """Manages the LangGraph agent workflow and connects it to the MCP tool server."""

    def __init__(self):
        self.__graph = None
        self.__mcp_client = None
        self.__mcp_url = settings.mcp_url
        self._llm: BaseChatModel = LLMService().get_chat_model()

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
            logger.error("Failed to initialize MCP client: %s", e)
            raise

    def start(self, state: MainState):
        """Initializes session and passes updated state to chat node."""
        question = state.get("question")
        session_id = state.get("session_id")

        response = self._llm.invoke([HumanMessage(content=CHAT_SESSION_PROMPT.format(query=question))])
        try:
            db = SessionLocal()
            try:
                session_id = get_or_create_session(db, session_id, response.content.strip())
            finally:
                db.close()
        except Exception as e:
            logger.warning("Failed to create session for agent: %s", e)
        return {"session_id": session_id}

    def classify_intent(self, state: MainState) -> dict:
        """Determines if query is casual conversation or requires database tools."""
        query = (state.get("question") or "").strip().lower()

        # Fast heuristic checks to bypass LLM and save latency/tokens
        for pattern in CASUAL_PATTERNS:
            if re.search(pattern, query):
                logger.info("Matched casual pattern -> classified as 'casual'")
                return {"intent": "casual"}

        for pattern in DB_PATTERNS:
            if re.search(pattern, query):
                logger.info("Matched database pattern -> classified as 'database'")
                return {"intent": "database"}

        # LLM fallback for ambiguous queries
        try:
            prompt = INTENT_PROMPT.format(query=state.get("question") or "")
            response = self._llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().lower()
            intent = "database" if "database" in decision else "casual"
            logger.info("LLM classified query as '%s'", intent)
            return {"intent": intent}
        except Exception as e:
            logger.warning("Intent classification failed: %s; defaulting to 'database'", e)
            return {"intent": "database"}

    async def casual_chat(self, state: MainState) -> dict:
        """Handles casual chit-chat with a bare LLM call, skipping all MCP tools."""
        question = state.get("question")
        session_id = state.get("session_id")
        history = []

        if session_id:
            try:
                db = SessionLocal()
                try:
                    history = get_recent_messages(db, session_id, limit=6)
                finally:
                    db.close()
            except Exception as e:
                logger.warning("Failed to load session history for casual chat: %s", e)

        messages = [
            SystemMessage(content=CASUAL_SYSTEM_PROMPT),
            *history,
            HumanMessage(content=question),
        ]

        logger.info("Executing casual chat (no database tools loaded)")
        response = await self._llm.ainvoke(messages)
        ai_response = response.content

        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens = response.usage_metadata.get("input_tokens", 0)
            output_tokens = response.usage_metadata.get("output_tokens", 0)
            total_tokens = response.usage_metadata.get("total_tokens", 0)

        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

        logger.info("Token usage: %s", token_usage)
        logger.info("Tool calls: []")

        if session_id:
            try:
                db = SessionLocal()
                try:
                    save_message(db, session_id, "user", question)
                    save_message(db, session_id, "assistant", ai_response)
                finally:
                    db.close()
            except Exception as e:
                logger.warning("Failed to save conversation turn to MySQL: %s", e)

        return {
            "answer": ai_response,
            "token_usage": token_usage,
            "tool_calls": [],
        }

    async def ask_question(self, state: MainState):
        """Invokes the AI agent with database tools to generate a verified answer."""
        question = state.get("question")
        session_id = state.get("session_id")
        history = []

        if session_id:
            try:
                db = SessionLocal()
                try:
                    history = get_recent_messages(db, session_id, limit=6)
                finally:
                    db.close()
            except Exception as e:
                logger.warning("Failed to load session history for agent: %s", e)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *history,
            HumanMessage(content=question),
        ]
        tool_calls = []

        if self.__mcp_client is None:
            await self.initialize()

        # Discover tools dynamically from the MCP server and bind them to the LLM
        tools = await self.__mcp_client.get_tools()
        agent = create_agent(self._llm, tools)
        logger.info("Executing database agent with %d MCP tools", len(tools))
        result = await agent.ainvoke({"messages": messages})
        ai_response = result["messages"][-1].content
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        # Sum token usage across internal turns and log each tool call
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

        logger.info("Token usage: %s", token_usage)
        logger.info("Tool calls: %s", tool_calls)

        # Persist conversation turn to MySQL if session_id is provided
        if session_id:
            try:
                db = SessionLocal()
                try:
                    save_message(db, session_id, "user", question)
                    save_message(db, session_id, "assistant", ai_response)
                finally:
                    db.close()
            except Exception as e:
                logger.warning("Failed to save conversation turn to MySQL: %s", e)

        return {
            "answer": ai_response,
            "token_usage": token_usage,
            "tool_calls": tool_calls,
        }

    def session_router(self, state: MainState) -> str:
        """Determines workflow branch based on session presence."""
        if state.get("session_id") and state["session_id"] != "":
            return "classify_intent"
        return "start"

    def intent_router(self, state: MainState) -> str:
        """Routes between casual conversation and database agent."""
        if state.get("intent") == "casual":
            return "casual_chat"
        return "chat"

    def build_pipeline(self):
        """Compiles the multi-node LangGraph execution graph for chat requests."""
        if self.__graph is not None:
            return self.__graph

        pipeline = StateGraph(MainState)
        pipeline.add_node("start", self.start)
        pipeline.add_node("classify_intent", self.classify_intent)
        pipeline.add_node("casual_chat", self.casual_chat)
        pipeline.add_node("chat", self.ask_question)

        pipeline.add_conditional_edges(
            START,
            self.session_router,
            {
                "start": "start",
                "classify_intent": "classify_intent",
            },
        )
        pipeline.add_edge("start", "classify_intent")
        pipeline.add_conditional_edges(
            "classify_intent",
            self.intent_router,
            {
                "casual_chat": "casual_chat",
                "chat": "chat",
            },
        )
        pipeline.add_edge("casual_chat", END)
        pipeline.add_edge("chat", END)

        self.__graph = pipeline.compile()
        return self.__graph