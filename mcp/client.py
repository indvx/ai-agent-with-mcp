import asyncio
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    async with  streamable_http_client("http://localhost:8001/mcp") as (read_stream,write_stream,_):
        async with ClientSession(read_stream, write_stream) as session:
            #initialize 
            await session.initialize()

            #list tools
            tools =  await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")

            print("Getting tables...")
            result = await session.call_tool("get_tables")
            print("result", result.content)

            print("Listing users...")
            result = await session.call_tool("list_records", arguments={"table": "users"})
            print("result", result.content)
    
if __name__ == "__main__":
    asyncio.run(main())
