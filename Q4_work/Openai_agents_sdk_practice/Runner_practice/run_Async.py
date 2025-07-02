import asyncio
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel
from agents.tracing import provider
from agents.run import RunConfig
from dotenv import load_dotenv
import os

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError ("Gemini api key is nt set")

external_client = AsyncOpenAI(
    api_key= gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.5-flash",
    openai_client = external_client
)

config = RunConfig(
    model = model,
    model_provider= external_client,
    tracing_disabled= True
)

agent = Agent(
    name = "Assistant",
    instructions= "You are a helpful Assistant",
    model = model
)

# If we want to Run a Async then we make a Function first
# In Async method Code Run line by line if one task is doing then other task are hold if task complete than other thing happen.
async def main():
    # By default Runner.run is Async
    result = await Runner.run(agent,"What is the capital of pakistan",run_config=config)
    print(result.final_output)


asyncio.run(main())