from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI
from agents.run import RunConfig
from dotenv import load_dotenv
import os

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set")

external_client = AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai")

model = OpenAIChatCompletionsModel(
    model = "gemini-2.5-flash",
    openai_client=external_client,
)

config = RunConfig(
    model =model,
    model_provider = external_client,
    tracing_disabled= True
)

agent = Agent(
    name = "Doctor Agent",
    instructions = "You are a doctor agent that can answer questions and help with patient with their health.",
    model = model,

)

import asyncio

async def main():
    result = await Runner.run(agent, "The patient is having a headache and a fever. What is the cause of the headache and fever?", run_config=config)
    print(result.final_output)

asyncio.run(main())



