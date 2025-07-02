# from dataclasses import dataclass
# from agents import Agent, Runner, function_tool,AsyncOpenAI , OpenAIChatCompletionsModel
# from agents.run import RunConfig
# import os
# from dotenv import load_dotenv


# load_dotenv()

# gemini_api_key = os.getenv("GEMINI_API_KEY")

# if not gemini_api_key:
#     raise ValueError("Gemini api key is not set")

# external_client = AsyncOpenAI (
#     api_key= gemini_api_key,
#     base_url= "https://generativelanguage.googleapis.com/v1beta/openai"
# )

# model = OpenAIChatCompletionsModel(
#     model = "gemini-2.0-flash",
#     openai_client=external_client,
# )

# config = RunConfig(
#     model = model,
#     model_provider= external_client,
#     tracing_disabled= True
# )

# @dataclass
# class UserContext:
#     uid: str
#     is_pro_user: bool

# @function_tool
# def greet_user(context: UserContext) -> str:
#     """Give a personalized greeting based on user's status."""
#     if context.is_pro_user:
#         return f"Hello Pro user {context.uid}, welcome back!"
#     else:
#         return f"Hello {context.uid}, upgrade to Pro for more features!"
    
# agent = Agent[UserContext](
#     name="Simple Greeter",
#     instructions="Greet the user based on their account type using the tool greet_user.",
#     tools=[greet_user],
#     model=model
# )

# pro_user = UserContext(uid="alice123", is_pro_user = True)
# free_user = UserContext(uid="bob456", is_pro_user = False)

# print("\n--- Pro User ---")
# result = Runner.run_sync(agent, "Please greet me", context=pro_user)
# print(result.final_output)

# print("\n--- Free User ---")
# result = Runner.run_sync(agent, "Please greet me", context=free_user)
# print(result.final_output)



import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Gemini API key is not set")

# Configure Gemini
genai.configure(api_key=gemini_api_key)

# Initialize the model
model = genai.GenerativeModel(model_name="gemini-1.5-flash")  # "2.0" branding isn't in SDK yet

# Context class (for clarity only)
class UserContext:
    def __init__(self, uid, is_pro_user):
        self.uid = uid
        self.is_pro_user = is_pro_user

# Simulate tool
def greet_user(context: UserContext) -> str:
    if context.is_pro_user:
        return f"Hello Pro user {context.uid}, welcome back!"
    else:
        return f"Hello {context.uid}, upgrade to Pro for more features!"

# Simulate agent with manual tool selection
def generate_response(user_input: str, context: UserContext):
    # Very basic routing — Gemini won't call `greet_user()` automatically
    if "greet" in user_input.lower():
        return greet_user(context)
    else:
        prompt = f"The user said: {user_input}. Context: uid={context.uid}, is_pro_user={context.is_pro_user}"
        response = model.generate_content(prompt)
        return response.text

# Testing
pro_user = UserContext(uid="alice123", is_pro_user=True)
free_user = UserContext(uid="bob456", is_pro_user=False)

print("\n--- Pro User ---")
print(generate_response("Please greet me", pro_user))

print("\n--- Free User ---")
print(generate_response("Please greet me", free_user))
