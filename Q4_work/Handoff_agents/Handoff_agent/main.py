from agents import Agent,Runner,function_tool,AsyncOpenAI,OpenAIChatCompletionsModel
from dotenv import load_dotenv
import requests
import os

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)


@function_tool
def get_daniyal_info():
    response =requests.get("https://my-api-navy-ten.vercel.app/")
    result = response.json()
    return result 

greeting_agent = Agent(
    name = "Greeting Agent",
    instructions="You are a greeting agent , your task is to greet user when user say's Hello,Hi & similar this words or greeting words ",
    model=model
)

daniyal_info_agent = Agent(
    name = "Muhammad Daniyal info Agent",
    instructions="You are a helpful assistant for Muhammad Daniyal"
    "your task is to help the user's understand about him"
    "You ALWAYS have to use get_daniyal_info tool to get the information about Muhammad Daniyal",
    tools=[get_daniyal_info],
    model=model
)

coordinator_agent = Agent(
    name= "Coordinator Agent",
    instructions="You are a routing/coordinator Agent"
    "Your task is to use the given agents to answer the user's question's"
    ,
    handoffs=[greeting_agent,daniyal_info_agent],
    model=model
)

input_value = input("Enter your prompt/question: ")
agent_result = Runner.run_sync(coordinator_agent,input_value)
print(agent_result.final_output)
