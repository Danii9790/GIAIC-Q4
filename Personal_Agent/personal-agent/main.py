import os
import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.tool import function_tool
import requests

load_dotenv()

# Gemini API key load karo
gemini_api_key = os.getenv("GEMINI_API_KEY")

# OpenAI client initialize karo with Gemini provider
provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

# Language model setup
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)


# ✅ Tool: Get personal info using your FastAPI

@function_tool("get_info")
def get_info() -> str:
    """
    Fetches profile data about Muhammad Daniyal from his personal API endpoint.

    This function makes a request to Muhammad Daniyal API and returns information
    about his background, skills, projects, education, work experience, and achievements & fetch all api data.

    Returns:
        str: JSON string containing Muhammad Daniyal profile information
    """

    try:
        response = requests.get("https://my-api-navy-ten.vercel.app/")
        if response.status_code == 200:
            return response.text
        else:
            return f"Error fetching data: Status code {response.status_code}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"


# 🧠 Agent Configuration
agent = Agent(
    name="Personal Assistant Agent",
    instructions="""
You are an assistant for Muhammad Daniyal.

1. If the user says "Hi", "Hello", or "Salam", reply:
   "Aslam alukum from Muhammad Daniyal!"

2. If the user says "Bye" or "Allah Hafiz","thanks" reply:
   "ALLAH HAFIZ"

3. If the user asks questions like:
   - What's your name?
   - Where do you live?
   - Which university do you go to?
   - What are your interests?
   - Education related questions.
   - family related questions.
   - currently enrolled courses.
   - and other api data related questions.
   - If someone ask about muhammad daniyal linkin,gmail,facebook account link fetch data or link's from get_info tool.
    or api.
   - If user ask the weekly plan of muhammad daniyal then fetch data from get_info tool.
   Use the `get_info` tool to answer.
   - if the ask about skill's of Muhammad daniyal fetch the skill's data from get_info tool.
   - if the user want to gmail account of Muhammad daniyal then fetch data from get_info tool.
   - if someone ask about where muhammad daniyal complete his ssc & hssc fetch data from get_info tool. 
4. Check and fetch api correctly first then fetch data correctly and then answer all the user questions?. 
5. If the user responds with "yes", "no", or "ok" (or similar short replies), politely prompt them to provide more context or ask a specific question so that I can assist them better.
6. For anything else, say:
   "I only respond to greetings, or questions about Muhammad Daniyal."

""",
    model=model,
    tools=[get_info]
)


# 🟢 Chat Start Handler
@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content="Hello and welcome! I’m the AI assistant of Muhammad Daniyal. Would you like to know more about him or explore something specific?"
    ).send()


# 🗣 Chat Message Handler
@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    result = await cl.make_async(Runner.run_sync)(agent, input=history)

    response_text = result.final_output
    await cl.Message(content=response_text).send()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
