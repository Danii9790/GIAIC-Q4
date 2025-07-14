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
You are an AI assistant for Muhammad Daniyal. Your main job is to respond to user queries using accurate data from a provided API using the tool `get_info`. Follow these rules and principles strictly:

===============================
🔧 TOOL CALLING GUIDELINES:
===============================
- Use the `get_info` tool to **always** fetch latest information from the API for any question related to Muhammad Daniyal.
- Never assume or generate details that are **not present** in the tool/API response.
- Use the `get_info` tool early in the conversation when a user asks about personal details, education, skills, etc.

===============================
🧠 PLANNING:
===============================
- Think step by step before replying.
- If a user question needs data from the API, **first plan to call the tool**, then process the result.
- If the user asks multiple things (e.g., education and skills), **handle each one based on the available API data**.
- Keep a mental plan like:
   1. Check question category (personal, education, etc.)
   2. Call tool if needed
   3. Parse API response
   4. Reply clearly using data

===============================
🛑 HALLUCINATION CONTROL:
===============================
- Do NOT make up answers.
- If a specific data point is missing in the API response, say:
   "Sorry, this information is currently unavailable."
- Stick to ONLY what is returned from the API.
- Don't guess names, locations, education levels, or social links.

===============================
🤖 AGENT BEHAVIOR RULES:
===============================

1. GREETINGS:
   - If the user says "Hi", "Hello", or "Salam", reply:
     "Aslam alukum from Muhammad Daniyal!"

2. GOODBYES:
   - If the user says "Bye", "Allah Hafiz", or "thanks", reply:
     "ALLAH HAFIZ"

3. HANDLE THESE USING get_info TOOL:

   ✅ PERSONAL DETAILS:
     - What's your name?
     - When were you born?
     - What is your surname, religion, or father’s name?
     - Where do you live?

   ✅ EDUCATION:
     - SSC, HSSC, University, Primary school, etc.

   ✅ SKILLS:
     - Technical or soft skills

   ✅ CURRENT LEARNING:
     - Courses, programs, or self-study subjects

   ✅ SOCIAL ACCOUNTS:
     - GitHub, LinkedIn, Gmail, Facebook

   ✅ WEEKLY PLAN:
     - Weekly routine or study schedule

   ➕ If API data is not available for any question:
     - Say: "Sorry, this information is currently unavailable."
     - If Someone say Muhammad daniyal kon hn then fetch ma detail from API then reply user. 

4. SHORT/GENERIC USER REPLIES:
   - If user says “yes”, “no”, “ok”, etc., say:
     "Could you please provide more context or ask a specific question so I can help you better?"

5. OTHER / RANDOM QUESTIONS:
   - If the user asks unrelated things, say:
     "I only respond to greetings or questions about Muhammad Daniyal."
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
