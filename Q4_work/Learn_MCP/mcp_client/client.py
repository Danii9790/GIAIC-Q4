# from ast import arg
# import asyncio
# from inspect import stack
# from mcp import ClientSession
# from mcp.client.streamable_http import streamablehttp_client
# from contextlib import AsyncExitStack
# import rich
# class MCPClient:
#     def __init__(self,url):
#         self.url = url
#         self.stack = AsyncExitStack() 
#         self._sess = None
    
#     async def list_tools(self):
#         async with self.session as session:
#             response = (await session.list_tools()).tools
#             return response
#     async def __aenter__(self): 
#         # Pizza Shop --> Counter ka banda jo Customer sy deal kr raha hn (Connection)
#         read,write,_ = await self.stack.enter_async_context(
#             streamablehttp_client(self.url)
#         )
#         # Backend jaha Pizza bana raha hn (All backend Done by )
#         self._sess = await self.stack.enter_async_context(
#             ClientSession(read,write)
#         )
#         await self._sess.initialize()
#         return self
#     async def __aexit__(self,*args):
#         await self.stack.aclose()

#     async def list_tools(self):
#         return (await self._sess.list_tools()).tools

    
#     async def call_tools(self,tool_name,*args,**kwards):
#         return await self._sess.call_tool(tool_name,*args,**kwards)
        

# async def main():
#     async with MCPClient("http://localhost:8000/mcp") as client:
#         tools = await client.list_tools()
#         rich.print(tools,"tools")

#         for tool in tools:
#             result = await client.call_tools(tool.name,{"name":"Daniyal"})
#             rich.print(f"Tool '{tool.name}' output:", result)

# asyncio.run(main())

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from contextlib import AsyncExitStack
import rich

class MCPClient:
    def __init__(self, url):
        self.url = url
        self.stack = AsyncExitStack()
        self._sess = None

    async def __aenter__(self):
        read, write, _ = await self.stack.enter_async_context(
            streamablehttp_client(self.url)
        )
        self._sess = await self.stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._sess.initialize()
        return self

    async def __aexit__(self, *args):
        await self.stack.aclose()

    async def list_tools(self):
        return (await self._sess.list_tools()).tools

    async def call_tools(self, tool_name, *args, **kwargs):
        return await self._sess.call_tool(tool_name, *args, **kwargs)


async def main():
    async with MCPClient("http://localhost:8000/mcp") as client:
        tools = await client.list_tools()
        rich.print(tools, "tools")

        for tool in tools:
            result = await client.call_tools(tool.name, {"name": "Daniyal"})
            rich.print(f"Tool '{tool.name}' output:", result)

asyncio.run(main())
