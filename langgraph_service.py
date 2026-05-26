from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()


from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


class MainState(TypedDict):
    question: Optional[str]
    answer: Optional[str]


llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"), 
    temperature=0, 
    verbose=True
    )


class LanggraphService:
    def __init__(self):
        self.__graph = None
        self.__mcp_client = None

    async def initialize(self):
        self.__mcp_client = MultiServerMCPClient(
            {
                "db_operation": {
                    "transport": "streamable_http",
                    "url": "http://localhost:8001/mcp",
                }
            }
        )
        return self.__mcp_client

    async def ask_question(self, state: MainState):
        question = state.get("question")
        messages = []
        messages.append(HumanMessage(content=question))

        tools = await self.__mcp_client.get_tools()
        agent = create_agent(llm, tools)
        result = await agent.ainvoke({"messages": messages})

        ai_response = result["messages"][-1].content

        return {"answer": ai_response}

    def build_pipeline(self):
        if self.__graph is not None:
            return self.__graph

        pipeline = StateGraph(MainState)
        pipeline.add_node("chat", self.ask_question)
        pipeline.add_edge(START, "chat")
        pipeline.add_edge("chat", END)

        self.__graph = pipeline.compile()
        return self.__graph
