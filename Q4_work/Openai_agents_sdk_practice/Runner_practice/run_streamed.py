import asyncio
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel
from agents.tracing import provider
from agents.run import RunConfig
from dotenv import load_dotenv
import os

from openai.types.responses import ResponseTextDeltaEvent

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

# Async Function using streaming
async def main():
    print("=== Starting Streaming ====")

    # Get the streaming result
    result = Runner.run_streamed(agent,"write a 500 words on AI",run_config=config)
    # Processing the streaming Events
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
            print(event.data.delta,end="",flush=True)
        
    print("==== Streaming Complete ====")

if __name__ == "__main__":
    asyncio.run(main())