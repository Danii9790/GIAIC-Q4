from agents import Agent, ModelSettings,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,function_tool,ModelSettings
from dotenv import load_dotenv
import os
from agents.agent import StopAtTools
from agents.run import RunConfig

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError ("Gemini api key is not set")

external_client =AsyncOpenAI(
    api_key= gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

model = OpenAIChatCompletionsModel(
    model= "gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled= True
)

@function_tool()

def get_addition(a: int , b:int) -> int:
    """Add two Numbers"""
    print("Tool Called........")
    return a + b - 5

@function_tool()
def human_review():
    """Human in the loop """
    print("Human_review is Called")
    return "Human in the loop Called "

agent = Agent(
    name = "Assistant",
    instructions="You are a helpful Assisant",
    tools=[get_addition,human_review],
    # tool_use_behavior="stop_on_first_tool",  # agent stop after the first agent is called
    # tool_use_behavior="run_llm_again",
    tool_use_behavior=StopAtTools(stop_at_tool_names=["human_review"])
    # model_settings=ModelSettings(tool_choice="none")
)

result = Runner.run_sync(agent, input= "What is 2 plus 2? After the result ask the human review",run_config=config)

print(result.final_output)