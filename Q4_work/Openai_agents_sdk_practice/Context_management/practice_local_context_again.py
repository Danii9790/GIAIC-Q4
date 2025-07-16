from dataclasses import dataclass
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel, function_tool , RunContextWrapper
from dotenv import load_dotenv
import os
import asyncio
from local_context import config
from local_context import model


load_dotenv()

@dataclass
class UserInfo:
    name : str
    uid : int
    age :int
    location : str = "Pakistan"

@function_tool
async def fetch_user_age(wrapper : RunContextWrapper[UserInfo]):
    '''Returns the Information of the User '''
    return f"User {wrapper.context.name} is {wrapper.context.age} Year's Old."

@function_tool
async def fetch_user_loaction(wrapper : RunContextWrapper[UserInfo]):
    '''Returns the User Location'''
    return f"User : {wrapper.context.name} is from {wrapper.context.location}."

async def main():
    user_obj = UserInfo("Muhammad Daniyal",34,21)

    agent = Agent[UserInfo](
        name = "Assistant",
        # Agent Run Perfectly With Context If Instructions is Is Provided to Agent.
        instructions="You are a Helpful Assistant.Your Work to response User with Friendly Message.",
        tools=[fetch_user_age,fetch_user_loaction],
        model = model
    )

    result = await Runner.run(starting_agent=agent,input="What is the age of user and Current Location of his/her?",context=user_obj,run_config=config)

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
