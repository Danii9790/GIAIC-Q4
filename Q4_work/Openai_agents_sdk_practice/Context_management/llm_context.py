from dataclasses import dataclass
from agents import Agent,Runner,RunContextWrapper,function_tool
import asyncio
from local_context import config
from local_context import model
from typing import Literal

@dataclass
class UserInfo:
    name: str
    uid: int

@function_tool
async def greet_user(context: RunContextWrapper[UserInfo], greeting: str) -> str:
  """Greets the User with their name.
  Args:
    greeting: A specialed greeting message for user
  """
  name = context.context.name
  return f"Hello {name}, {greeting}"

async def main():
    user_info = UserInfo(name="User", uid=34)

    agent = Agent[UserInfo](
        name="Assistant",
        tools=[greet_user],
        model=model,
        # Dynamic function context pass in instructions/system prompmt/developer prompt
        instructions="Always greet the user using <function_call>greet_user</function_call> and welcome from Muhammad Daniyal"
    )

    result = await Runner.run(
        starting_agent=agent,
        input="Hello",
        context=user_info,
        run_config=config
    )

    print(result.final_output)

asyncio.run(main())