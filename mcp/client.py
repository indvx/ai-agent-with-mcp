import asyncio
from dotenv import load_dotenv
load_dotenv()

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    async with streamable_http_client("http://localhost:8001/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")

            print("Listing available database tables...")
            result = await session.call_tool("get_tables")
            print("tables:", result.content)

            print("Example: list records from a table")
            result = await session.call_tool("list_records", arguments={"table": "your_table"})
            print("records:", result.content)


if __name__ == "__main__":
    asyncio.run(main())
