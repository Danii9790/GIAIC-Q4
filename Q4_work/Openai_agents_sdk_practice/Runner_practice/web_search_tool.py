from agents import Agent, WebSearchTool, Runner , set_default_openai_key
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
set_default_openai_key(api_key)
model = os.environ.get("OPENAI_MODEL")

agent = Agent(
    name="Assistant",
    tools=[
        # Hosted-Tool =>  WebSearchTool
        WebSearchTool()
    ],
    model=model
)

async def main():
    result = await Runner.run(agent, "What is the weather of karachi")

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())

