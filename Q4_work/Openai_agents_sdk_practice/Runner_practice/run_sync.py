from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel
from agents.run import RunConfig
from dotenv import load_dotenv
import os


load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError ("Api Key is not set")

external_client = AsyncOpenAI(
    api_key= gemini_api_key,
    base_url= "https://generativelanguage.googleapis.com/v1beta/"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.5-flash",
    openai_client= external_client
)

config = RunConfig(
    model = model ,
    model_provider= external_client,
    tracing_disabled= True
)

agent = Agent(
    name = "Assistant",
    instructions= "You are a helpful and friendly response Assistant"
)

result = Runner.run_sync(agent,"Give me a short note related to AI",run_config=config)
print(result.final_output)


