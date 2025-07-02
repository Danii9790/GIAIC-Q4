from agents.models import openai_chatcompletions
from agents.tracing import provider
from pydantic import BaseModel, config
from agents import Agent, Runner, AsyncOpenAI , OpenAIChatCompletionsModel 
from agents.run import RunConfig
import asyncio
import os
from dotenv import load_dotenv

from tools_example import external_client, gemini_api_key

# Load your OpenAI API key from the .env file
load_dotenv()
gemini_api_key =  os.getenv("GEMINI_API_KEY")
 
external_client = AsyncOpenAI(
    api_key= gemini_api_key,
    base_url= "https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.0-flash",
    openai_client = external_client
)

config = RunConfig(
    model = model,
    model_provider = external_client,
    tracing_disabled= True

)

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

# Step 2: Create an agent that uses this model
agent = Agent(
    name="Simple Calendar Agent",
    instructions="Extract calendar events from the input text. Include event name, date, and participants.",
    output_type=CalendarEvent,  # 👈 This is the structured output!
    model=model
)

# Step 3: Run the agent

query = "Schedule a team meeting called 'Sprint Review' on July 3rd with Alice, Bob, and Charlie."
result = Runner.run_sync(agent, query,run_config=config)
print("\nStructured Output:")
print(result.final_output)  # This will be a CalendarEvent object!