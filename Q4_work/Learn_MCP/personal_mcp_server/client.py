# # client.py
# import asyncio
# from contextlib import AsyncExitStack
# from mcp import ClientSession
# from mcp.client.streamable_http import streamablehttp_client
# import rich

# class MCPClient:
#     def __init__(self, url):
#         self.url = url
#         self.stack = AsyncExitStack()
#         self._sess = None

#     async def __aenter__(self):
#         read, write, _ = await self.stack.enter_async_context(
#             streamablehttp_client(self.url)
#         )
#         self._sess = await self.stack.enter_async_context(
#             ClientSession(read, write)
#         )
#         await self._sess.initialize()
#         return self

#     async def __aexit__(self, *args):
#         await self.stack.aclose()

#     async def list_tools(self):
#         return await self._sess.list_tools()

#     async def call_tool(self, tool_name, params=None):
#         if params is None:
#             params = {}
#         # call_tool returns result object; we return result["result"] or the raw
#         res = await self._sess.call_tool(tool_name, params)
#         return res

# async def main():
#     url = "http://localhost:8000/mcp"   # streamable-http endpoint that FastMCP serves
#     async with MCPClient(url) as client:
#         tools = await client.list_tools()
#         rich.print("Tools from server:", tools)
#         # find get_info
#         for t in tools:
#             # representation might be object/dict depending on SDK version
#             name = getattr(t, "name", None) or t.get("name") if isinstance(t, dict) else str(t)
#             rich.print("-> tool name:", name)

#         # call get_info if present
#         rich.print("Calling get_info...")
#         result = await client.call_tool("get_info")
#         rich.print("get_info result:", result)

# if __name__ == "__main__":
#     asyncio.run(main())
# client.py
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from rich import print as rprint

class MCPClient:
    def __init__(self, url: str):
        self.url = url
        self.stack = AsyncExitStack()
        self._sess: ClientSession | None = None

    async def __aenter__(self):
        read, write, _ = await self.stack.enter_async_context(
            streamablehttp_client(self.url)
        )
        self._sess = await self.stack.enter_async_context(ClientSession(read, write))
        await self._sess.initialize()
        return self

    async def __aexit__(self, *args):
        await self.stack.aclose()

    async def list_tools(self):
        return await self._sess.list_tools()

    async def call_tool(self, tool_name: str, params: dict | None = None):
        params = params or {}
        return await self._sess.call_tool(tool_name, params)

async def main():
    url = "http://127.0.0.1:8000/mcp"
    async with MCPClient(url) as client:
        tools = await client.list_tools()
        rprint("[bold green]Tools from server:[/]", tools)

        rprint("[bold cyan]Calling get_info...[/]")
        res = await client.call_tool("get_info")
        rprint("[bold magenta]get_info result:[/]", res)

if __name__ == "__main__":
    asyncio.run(main())