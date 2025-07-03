from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel
from agents.run import RunConfig
from dotenv import load_dotenv
import os
from pydantic import BaseModel,Field
from typing import List
import asyncio

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Api key is not set")

external_client = AsyncOpenAI(
    api_key= gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.5-flash",
    openai_client= external_client
)

config = RunConfig(
    model = model,
    model_provider= external_client,
    tracing_disabled = True
)

class TravelPlan(BaseModel):
    destination : str
    duration_days : int
    budget : float
    activities : List[str] = Field(description="List of recommended activities")
    notes : str = Field(description="Additional notes or recommendations")

# Main Travel Agent

travel_agent = Agent (
    name = "Travel Planner",
    instructions="""
    You are a comprehensive travel planning assistant that helps users plan their perfect trip.
    
    You can create personalized travel itineraries based on the user's interests and preferences.
    
    Always be helpful, informative, and enthusiastic about travel. Provide specific recommendations
    based on the user's interests and preferences.
    
    When creating travel plans, consider:
    - Local attractions and activities
    - Budget constraints
    - Travel duration
    """,
    model = model,
    output_type= TravelPlan
)

# Main Function
async def main():
    # Example queries to test the System 
    queries = [
        "I'm Planning a trip karachi to Sawat for 5 days with a budget of 30k . What should i do there?",
        "I want to visit Lahore for a week with a budget of 20k . What activities do you recommanded?"
    ]

    for query in queries:
        print("\n" + "="*50)
        print(f"Query : {query}")

        result = await Runner.run(travel_agent,query,run_config=config)

        print("\nFinal Output")
        travel_plan = result.final_output

        # Format the output
        print(f"\n🌍 TRAVEL PLAN FOR {travel_plan.destination.upper()} 🌍")
        print(f"Duration: {travel_plan.duration_days} days")
        print(f"Budget: ${travel_plan.budget}")
        
        print("\n🎯 RECOMMENDED ACTIVITIES:")
        for i , activity in enumerate(travel_plan.activities,1):
            print(f"{i}.{activity}")

        print(f"\n Notes : {travel_plan.notes}")

if __name__ == "__main__":
    asyncio.run(main())


