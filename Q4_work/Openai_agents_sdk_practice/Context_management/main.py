import asyncio
from json import load
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel, agent, tracing,function_tool , RunContextWrapper
from agents.run import RunConfig
from dotenv import load_dotenv
import os
from dataclasses import dataclass

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Gemini API Key is not set")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model = model,
    model_provider=external_client,
    tracing_disabled= True   
)

@dataclass
class Userinfo:
    name : str
    uid : int
    age : int

@function_tool
async def fetch_user_info(wrapper : RunContextWrapper[Userinfo]) -> str:
    return f"ID : {wrapper.context.uid}  Name : {wrapper.context.name} is {wrapper.context.age} Year's Old"

async def main():
    user_info_obj = Userinfo(name="Daniyal",uid=34,age=21)
    agent = Agent[Userinfo](
        name = "Assistant",
        instructions="You are a helpful Agent . Always use fetch_user-info Tool and only response exactly what the tool returns.",
        tools=[fetch_user_info]
    )
    result = await Runner.run(agent,"what is the user id,name,age?",context=user_info_obj,run_config=config)

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
