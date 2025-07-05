import asyncio
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,ModelSettings
from agents.exceptions import (
    AgentsException,
    MaxTurnsExceeded,
    ModelBehaviorError,
    UserError,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered)
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
# Define an agent
agent = Agent(
    name="FaultyAgent",
    instructions="Produce invalid output to test error handling.",
    model=model
)

try:
    # Try a normal run (this will work fine unless the model misbehaves)
    result = Runner.run_sync(agent, "Tell me a story about a cat who codes.",run_config=config)
    # For testing Raise a Error
    raise AgentsException("Inalvid sdk error")
    # Final Response
    print("Final Output:", result.final_output)

except MaxTurnsExceeded:
    print("❌ Error: The conversation exceeded the allowed number of turns.")

except ModelBehaviorError:
    print("❌ Error: The model gave a bad response (e.g. invalid JSON).")

except InputGuardrailTripwireTriggered:
    print("🚨 Guardrail Triggered: The input didn't meet safety/validation rules.")

except OutputGuardrailTripwireTriggered:
    print("🚨 Guardrail Triggered: The output failed validation or policy checks.")

except UserError:
    print("❌ UserError: You likely made a mistake in how you used the SDK.")

except AgentsException as e:
    print(f"⚠️ General SDK Exception: {e}")

except Exception as e:
    print(f"🔥 Unexpected Error: {e}")
