import asyncio
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,ModelSettings
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
    tracing_disabled= True,
    model_settings=ModelSettings(temperature=0.8),
    workflow_name="Creative_run",
)

async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.",model=model)

    # First turn
    result = await Runner.run(agent, "What is the founder of pakistan?",run_config=config)
    print(result.final_output)
    # Expected Answer : Muhammad ALi Jinnah

     # Second turn
    new_input = result.to_input_list() + [{"role": "user", "content": "Where he is born?"}]
    result = await Runner.run(agent, new_input,run_config=config)
    print(result.final_output)
    # Expected Answer : Karachi
if __name__ =='__main__':
    asyncio.run(main())