import asyncio
import os
from dotenv import load_dotenv, find_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from agents.mcp import MCPServerStreamableHttp,MCPServerStreamableHttpParams

_: bool = load_dotenv(find_dotenv())

# ONLY FOR TRACING
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

# 1. Which LLM Service?
external_client: AsyncOpenAI = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 2. Which LLM Model?
llm_model: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

@function_tool
def get_weather(city: str) -> str:
    """A simple function to get the weather for a user."""
    return f"The weather for {city} is sunny."

async def main():
    param_config = MCPServerStreamableHttpParams(url="http://localhost:8000/mcp/")
    async with MCPServerStreamableHttp(params=param_config,name="HelloMCP") as mcp_hello_server:
        base_agent: Agent = Agent(
            name="Greeting agent",
            instructions="You are a helpful assistant.",
            model=llm_model,    
            mcp_servers=[mcp_hello_server]
        )


        res = await Runner.run(base_agent, "who is muhammad daniyal?")
        print(res.final_output)

if __name__ =="__main__":
    asyncio.run(main())

