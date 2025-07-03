from signal import raise_signal
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,function_tool
from agents.run import RunConfig
from dotenv import load_dotenv
import os
from typing import List
from pydantic import BaseModel,Field
import requests
import asyncio

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Api key is not set")

external_client = AsyncOpenAI(
    api_key = gemini_api_key,
    base_url= "https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.0-flash",
    openai_client= external_client
)

config = RunConfig(
    model = model,
    model_provider= external_client,
    tracing_disabled= True
)

class Travel_plan(BaseModel):
    destination : str
    duration_days : int
    budget : float
    activities : List[str] = Field(description="List of recommended activities")
    notes : List[str] = Field(description="Additional notes or recommendations")

@function_tool
def get_weather(location: str, unit: str = "C") -> str:
    """
    Fetch the weather for a given location using OpenWeatherMap API.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather API key not set."

    units = "metric" if unit == "C" else "imperial"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&units={units}&appid={api_key}"

    try:
        response = requests.get(url)
        data = response.json()
        
        print("DEBUG WEATHER RESPONSE:", data)

        if response.status_code != 200:
            return f"Sorry, I couldn't find the weather for '{location}'."

        weather_desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]

        return f"The weather in {location} is {weather_desc} with a temperature of {temp}°{unit}. Feels like {feels_like}°{unit}."

    except Exception as e:
        return f"An error occurred while fetching the weather: {str(e)}"



travel_agent = Agent (
    name = "Travel Planner",
    instructions="""
    You are a comprehensive travel planning assistant that helps users plan their perfect trip.
    
    You can:
    1. Provide weather information for destinations
    2. Create personalized travel itineraries
    
    Always be helpful, informative, and enthusiastic about travel. Provide specific recommendations
    based on the user's interests and preferences.
    
    When creating travel plans, consider:
    - The weather at the destination
    - Local attractions and activities
    - Budget constraints
    - Travel duration
    """,
    model = model,
    output_type= Travel_plan,
    tools=[get_weather]
)

async def main():
    User_input = input("Enter your Traveling plan : ")
    result = await Runner.run(travel_agent,User_input,run_config=config)

    print("\nFinal Response")
    travel_plan = result.final_output

    # format the output
    print(f"\n Travel Plan For {travel_plan.destination.upper()}.")
    print(f"\n Duration : {travel_plan.duration_days} days.")
    print(f"\n Budget : ${travel_plan.budget}.")

    print("\n RECOMMENDED ACTIVITIES ")
    for i ,activity in enumerate(travel_plan.activities,1):
        print(f" {i} . {activity}")
    
    print(f"\n Notes : {travel_plan.notes}")

if __name__ == "__main__":
    asyncio.run(main())