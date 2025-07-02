from agents.models import openai_chatcompletions
from agents.tracing import provider
from pydantic import BaseModel, config
from agents import Agent, Runner, AsyncOpenAI , OpenAIChatCompletionsModel 
from agents.run import RunConfig
import asyncio
import os
from dotenv import load_dotenv
from dataclasses import dataclass

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

# Define a simple user context
@dataclass
class UserContext:
    name: str
    is_premium: bool

# Dynamic instructions function
def dynamic_instructions(context, agent) -> str:
    user_name = context.context.name
    if context.context.is_premium:
        return f"Hello {user_name}! You are a premium user. Give detailed premium support."
    else:
        return f"Hello {user_name}! Provide standard support."

# Create agent using dynamic instructions
agent = Agent[UserContext](
    name="Dynamic Agent",
    instructions=dynamic_instructions,
    model=model
)

# Run the agent for different users

# Premium user
premium_user = UserContext("Alice", True)
print("\n--- Premium User ---")
result1 = Runner.run_sync(agent, "What support do I have access to?", context=premium_user,run_config=config)
print(result1.final_output)

# Free user
free_user = UserContext("Bob", False)
print("\n--- Free User ---")
result2 = Runner.run_sync(agent, "What support do I have access to?", context=free_user,run_config=config)
print(result2.final_output)