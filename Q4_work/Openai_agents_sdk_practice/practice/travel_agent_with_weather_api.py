from signal import raise_signal
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.tool import function_tool
from agents.run import RunConfig
from dotenv import load_dotenv
import os
from typing import List
from pydantic import BaseModel, Field
import requests
import asyncio

# Load environment variables
load_dotenv()

# Load Gemini API Key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Setup OpenAI-like client for Gemini (your existing config - not changed)
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# Output format
class Travel_plan(BaseModel):
    destination: str
    duration_days: int
    budget: float
    activities: List[str] = Field(description="List of recommended activities")
    notes: List[str] = Field(description="Additional notes or recommendations")

# Function Tool: Weather API
@function_tool
def get_weather(location: str, unit: str = "C") -> str:
    """
    Returns weather information for a specific location using OpenWeatherMap API.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather API key not set."

    units = "metric" if unit == "C" else "imperial"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units={units}&appid={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return f"Sorry, I couldn't find the weather for '{location}'. ({data.get('message', 'No message')})"

        weather_desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]

        return f"The weather in {location} is {weather_desc} with a temperature of {temp}°{unit}. Feels like {feels_like}°{unit}."

    except Exception as e:
        return f"An error occurred while fetching the weather: {str(e)}"

# Agent Configuration
travel_agent = Agent(
    name="Travel Planner",
    instructions="""
You are a helpful travel planning assistant.

You MUST call the `get_weather` tool if the user input includes a city, destination, or country — to get the latest weather for that location.

Once you get the weather, use it to:
- Recommend suitable activities
- Give packing suggestions
- Include notes relevant to the weather

ALWAYS use the `get_weather(location)` tool BEFORE suggesting the travel plan. Do not guess the weather yourself.

Your response should include:
- Destination (from the user input)
- Duration in days (from user input)
- Budget (from user input)
- List of 3–5 activities
- Notes with suggestions

Return your final answer as a Travel_plan object.
""",

    model=model,
    output_type=Travel_plan,
    tools=[get_weather]
)

# Main Async Function
async def main():
    user_input = input("Enter your Traveling plan: ")
    result = await Runner.run(travel_agent, user_input, run_config=config)

    print("\nFinal Response")
    travel_plan = result.final_output

    print(f"\nTravel Plan For: {travel_plan.destination.upper()}")
    print(f"Duration: {travel_plan.duration_days} days")
    print(f"Budget: ${travel_plan.budget}")
    # print(f"\nCurrent Weather in {travel_plan.destination.title()}:\n{get_weather(travel_plan.destination)}")


    print("\nRecommended Activities:")
    for i, activity in enumerate(travel_plan.activities, 1):
        print(f"{i}. {activity}")

    print("\nNotes:")
    for note in travel_plan.notes:
        print(f"- {note}")

# Run Main
if __name__ == "__main__":
    asyncio.run(main())
