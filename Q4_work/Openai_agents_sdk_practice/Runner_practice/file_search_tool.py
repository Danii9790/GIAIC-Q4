from agents import Agent, FileSearchTool, Runner , set_default_openai_key
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
set_default_openai_key(api_key)
model = os.environ.get("OPENAI_MODEL")

agent = Agent(
    name="Assistant",
    tools=[
        # Hosted-Tool =>  FileSearchTool 
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_68690ab35bec8191a157343ab4deba53"],
        ),
    ],
    model=model
)

async def main():
    result = await Runner.run(agent, "What is Current position of Muhammad Daniyal")

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())

# Output From (LLM) model = gpt-4o
# Muhammad Daniyal is currently an Internship Trainee at DevelopersHub Corporation©, where he's gaining hands-on experience with AI/ML including machine learning models, data pipelines, and tools like Python, TensorFlow, and OpenAI APIs. Additionally, he is a student in the Governor Sindh Initiative for GenAI, Web3, and Metaverse.