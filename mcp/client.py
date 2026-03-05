import asyncio
from fastmcp import Client

async def run():
    client = Client('server.py')
    async with client:
        tools = await client.list_tools()

        tool = tools[0]
        tool_result = await client.call_tool(tool.name)
        print(tool_result)

if __name__ == '__main__':
    asyncio.run(run())