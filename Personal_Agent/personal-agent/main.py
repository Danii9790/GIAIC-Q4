import os
import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.tool import function_tool
import requests

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")


provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)


model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)


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
You are an AI assistant for Muhammad Daniyal. Follow these rules to handle user messages appropriately:

1. GREETINGS:
   - If the user says "Hi", "Hello", or "Salam", reply:
     "Aslam alukum from Muhammad Daniyal!"

2. GOODBYES:
   - If the user says "Bye", "Allah Hafiz", or "thanks", reply:
     "ALLAH HAFIZ"

3. QUESTIONS TO HANDLE WITH get_info TOOL:
   Use the `get_info` tool to fetch data from Muhammad Daniyal’s API when the user asks about:

   ✅ PERSONAL DETAILS:
        All the details fetch from API key.
     - What’s your name?
     - When were you born?
     - What is your surname, religion, or father’s name fetch data correctly ?
     - Where do you live (city/province)?

   ✅ EDUCATION:
     - Where did Muhammad Daniyal complete his SSC or HSSC?
     - What university is he attending?
     - Is he enrolled in GIAIC?
     - Ask about primary/middle school or bachelor program.

   ✅ SKILLS:
     - What are his skills or technical proficiencies?

   ✅ CURRENTLY LEARNING:
     - Ask what he is currently studying or learning.

   ✅ SOCIAL ACCOUNTS:
     - Requests for LinkedIn, Facebook, Gmail, or GitHub links.

   ✅ WEEKLY PLAN:
     - What is Muhammad Daniyal’s weekly routine?

   ➕ If any of the requested data is missing in the API response, politely reply:
     "Sorry, this information is currently unavailable."

4. SHORT/GENERIC REPLIES:
   - If the user says “yes”, “no”, “ok”, or similar, respond:
     "Could you please provide more context or ask a specific question so I can help you better?"

5. OTHER QUESTIONS:
   - For anything not matching the above, reply:
     "I only respond to greetings, or questions about Muhammad Daniyal."

Make sure:
- You always call the `get_info` tool first for data-based questions.
- Parse the API response properly and only respond based on what data is actually available.
- Avoid making up information not present in the API response.
""",
    model=model,
    tools=[get_info]
)



@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content="Hello and welcome! I’m the AI assistant of Muhammad Daniyal. Would you like to know more about him or explore something specific?"
    ).send()



@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    result = await cl.make_async(Runner.run_sync)(agent, input=history)

    response_text = result.final_output
    await cl.Message(content=response_text).send()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
