from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI , function_tool
from dotenv import load_dotenv
from agents.run import RunConfig
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
    model = model,
    model_provider = external_client,
    tracing_disabled= True
)

@function_tool
def get_weather(city: str) -> str:
    """Get the weather of a city"""
    return f"The weather of {city} is sunny"

agent = Agent(
    name = "Weather Agent",
    instructions = "You are a weather agent that can answer questions about the weather.",
    model = model,
    tools = [get_weather],
)

result = Runner.run_sync(agent, "What is the weather in Tokyo?", run_config=config) 
print(result.final_output)