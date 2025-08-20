import os
import json
from agents.run import RunConfig
import requests
import asyncio
from dotenv import load_dotenv

import streamlit as st

# Agents imports (keep same package you were using)
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.tool import function_tool
from agents.run import RunConfig

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------------------
# Provider & Model setup
# ---------------------------
provider = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)

config = RunConfig(
    model = model,
    model_provider=provider
)
# ---------------------------
# Tool: get_info
# ---------------------------
@function_tool("get_info")
def get_info() -> str:
    """
    Fetches profile data about Muhammad Daniyal from his personal API endpoint.
    Returns JSON string with his details or an error message.
    """
    try:
        resp = requests.get("https://my-api-navy-ten.vercel.app/", timeout=10)
        if resp.status_code == 200:
            # return raw text (agent instructions require using tool output directly)
            return resp.text
        else:
            return json.dumps({"error": f"Status code {resp.status_code}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------
# Agent configuration
# ---------------------------
agent = Agent(
    name="Personal Assistant Agent",
    instructions="""
You are an AI assistant for Muhammad Daniyal. Your main job is to respond to user queries
using accurate data from the provided API using the tool `get_info`. Follow the tool-calling
guidelines and hallucination control rules in the original specification: always call get_info
for personal details, don't fabricate missing info, and reply with the exact phrases required
for greetings/goodbyes. If something is missing say: "Sorry, this information is currently unavailable."
    """,
    model=model,
    tools=[get_info],
)


st.set_page_config(page_title="Muhammad Daniyal — Personal Assistant", page_icon="🤖", layout="centered")
st.markdown(
    """
    <h1 style="text-align: center;">🤖 Muhammad Daniyal's AI Assistant</h1>
    """,
    unsafe_allow_html=True
)

# Initialize session history (stateful)
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "assistant", "content": "Hello and welcome! I’m the AI assistant of Muhammad Daniyal. Would you like to know more about him or explore something specific?"}
    ]

for msg in st.session_state.history:
    if msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    else:
        st.chat_message("user").write(msg["content"])


user_input = st.chat_input("Type your message here...")

if user_input:
    # Append and show user's message
    st.session_state.history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Ensure there's an event loop in this thread (fixes Streamlit RuntimeError)
    try:
        loop = asyncio.get_event_loop()
        # On some Python/Streamlit combos, get_event_loop() returns a loop but it may be closed.
        if loop.is_closed():
            raise RuntimeError("event loop closed")
    except Exception:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the agent asynchronously using the local loop
    try:
        # NOTE: Runner.run is expected to be an async coroutine that accepts the agent and input
        result = loop.run_until_complete(Runner.run(agent, input=st.session_state.history))
    except Exception as e:
        # Friendly error message in chat
        err_text = f"Error running the agent: {type(e).__name__} - {str(e)}"
        st.session_state.history.append({"role": "assistant", "content": err_text})
        st.chat_message("assistant").write(err_text)
    else:
        # Extract final_output safely
        response_text = getattr(result, "final_output", None) or getattr(result, "output", None) or str(result)
        # Append assistant response to history and display it
        st.session_state.history.append({"role": "assistant", "content": response_text})
        st.chat_message("assistant").write(response_text)


