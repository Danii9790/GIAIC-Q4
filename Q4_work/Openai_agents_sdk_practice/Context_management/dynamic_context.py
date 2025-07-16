from dataclasses import dataclass
from agents import Agent,Runner,RunContextWrapper
import asyncio
from local_context import config
from local_context import model
from typing import Literal
import random

@dataclass
class CustomContext:
    style: str

def custom_instructions(
    run_context : RunContextWrapper[CustomContext],agent : Agent[CustomContext]) -> str:
    context = run_context.context
    if context.style == "formal":
        return "Only Respond in Formal"
    elif context.style == "casual":
        return "Only Respond in Casual"
    else:
        return "Only Respond with formal/casual Language"
agent = Agent(
    name = "Chat Agent",
    instructions=custom_instructions,
    model=model
)

async def main():
    choice: Literal["formal", "casual"] = random.choice(["formal", "casual"])
    context = CustomContext(style=choice)
    print(f"Using Style : {choice}")
    user_prompt = "Greet Me"
    result = await Runner.run(agent,user_prompt,context=context,run_config=config)
    print(f"Assistant : {result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())

# Output's
"""
Using Style : formal
Assistant : It is a pleasure to make your acquaintance.
"""
"""
Using Style : casual
Assistant : Hey, what's up?
"""