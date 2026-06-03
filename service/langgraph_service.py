from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()


from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.runnables import RunnableConfig


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
        self.callback = UsageMetadataCallbackHandler()

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

    async def ask_question(
        self, state: MainState, config: Optional[RunnableConfig] = None
    ):
        question = state.get("question")
        messages = []
        messages.append(HumanMessage(content=question))

        tools = await self.__mcp_client.get_tools()
        agent = create_agent(llm, tools)

        run_config = dict(config or {})
        callbacks = run_config.get("callbacks")
        if callbacks is None:
            run_config["callbacks"] = [self.callback]
        elif isinstance(callbacks, list):
            if self.callback not in callbacks:
                run_config["callbacks"] = list(callbacks) + [self.callback]
        else:
            if hasattr(callbacks, "add_handler"):
                callbacks.add_handler(self.callback)

        result = await agent.ainvoke({"messages": messages}, config=run_config)

        ai_response = result["messages"][-1].content
        tool_calls = []
        for message in result["messages"]:
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append(tool_call)

        print("Token_Usage:", self.callback.usage_metadata)
        return {
            "answer": ai_response,
            "token_usage": self.callback.usage_metadata,
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
