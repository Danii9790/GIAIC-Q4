# agent_app.py
import os
import asyncio
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from agents.run import RunConfig

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

# Configure Gemini in OpenAI-compatible format
provider = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider,
)

config = RunConfig(model=model, model_provider=provider)

# Minimal MCP client helper
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

    async def call_tool(self, name: str, params: dict | None = None):
        params = params or {}
        return await self._sess.call_tool(name, params)

# Tool wrapper that calls the MCP server's get_info
@function_tool("get_info")
async def get_info() -> str:
    async with MCPClient("http://127.0.0.1:8000/mcp") as mcp:
        res = await mcp.call_tool("get_info")
        # Normalize result to a plain string
        try:
            if isinstance(res, dict):
                # Common shape: {"content": [{"type": "text", "text": "..."}], ...}
                if "content" in res and isinstance(res["content"], list):
                    parts = []
                    for c in res["content"]:
                        if isinstance(c, dict) and c.get("type") == "text":
                            parts.append(c.get("text", ""))
                    if parts:
                        return "\n".join(parts)
                if "result" in res and isinstance(res["result"], (str, bytes)):
                    return res["result"].decode() if isinstance(res["result"], bytes) else res["result"]
            return str(res)
        except Exception:
            return str(res)

agent = Agent(
    name="Personal Assistant Agent",
    instructions=(
        "You are an AI assistant for Muhammad Daniyal.\n"
        "Use the `get_info` tool to answer personal details, education, skills, etc.\n"
        "Never make up data; only use API response."
    ),
    model=model,
    tools=[get_info],
)

async def main():
    print("🤖 Personal MCP Agent Started! Type 'exit' to quit.")
    history = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break
        history.append({"role": "user", "content": user_input})
        result = await Runner.run(agent, input=history, run_config=config)
        print("Agent:", result.final_output)
        history.append({"role": "assistant", "content": result.final_output})

if __name__ == "__main__":
    asyncio.run(main())