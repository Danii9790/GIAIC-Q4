
from agents import Agent, Runner, AsyncOpenAI , OpenAIChatCompletionsModel 
from agents.run import RunConfig
import os
from dotenv import load_dotenv

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

#Define the sub-agent for handling orders
order_agent = Agent(
    name="Order Agent",
    instructions="You handle all questions about orders, shipping, and delivery.",
    model = model
)

# Define the sub-agent for handling support issues
support_agent = Agent(
    name="Support Agent",
    instructions="You handle support-related issues like login problems or account settings.",
    model = model
)

# Define the main agent that decides who should answer
main_agent = Agent(
    name="Main Agent",
    instructions="""
        You help customers with general questions.
        If the question is about orders, hand it off to the Order Agent.
        If it's about support, hand it off to the Support Agent.
    """,
    handoffs=[order_agent, support_agent],
    model = model
)

# Run an example

    # Test 1: Order-related question
print("\n--- Order Question ---")
result1 = Runner.run_sync(main_agent, "Where is my package?",run_config=config)
print(result1.final_output)

# Test 2: Support-related question
print("\n--- Support Question ---")
result2 = Runner.run_sync(main_agent, "I can't log in to my account.",run_config=config)
print(result2.final_output)