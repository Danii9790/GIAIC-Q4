import asyncio
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,ModelSettings
from agents.tracing import provider
from agents.run import RunConfig
from dotenv import load_dotenv
import os

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError ("Gemini api key is nt set")

external_client = AsyncOpenAI(
    api_key= gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

model = OpenAIChatCompletionsModel(
    model = "gemini-2.5-flash",
    openai_client = external_client
)

config = RunConfig(
    model = model,
    model_provider= external_client,
    tracing_disabled= True,
    model_settings=ModelSettings(temperature=0.8),
    workflow_name="Creative_run",
)

agent = Agent(
    name = "Summary Agent",
    instructions= "Summarize the user's message in 1 sentence.",
    model = model

)

result = Runner.run_sync(agent,"Explain the basic of AI",run_config=config)

# Acces useful properties from RunResult (inherits RunResultBase)

print("\n Final Output")
print(result.final_output)

print("\nLast Agent")
print(result.last_agent.name)

print("\n Original  Input :")
print(result.input)

print("\n New Items Generated :")
for item in result.new_items:
    print(f"- {item.type}")

print("\n Raw Response : ")
for response in result.raw_responses:
    print(response)

# Guardrails 
print("Input Guardrail Results : ",result.input_guardrail_results)
print("Output Guardrail Results : ",result.output_guardrail_results)
