# import os
# import json
# import requests
# import asyncio
# from dotenv import load_dotenv
# from contextlib import asynccontextmanager

# import streamlit as st
# os.makedirs(os.path.expanduser('~/.streamlit'), exist_ok=True)
# with open(os.path.expanduser('~/.streamlit/config.toml'), 'w') as f:
#     f.write("""
# [server]
# headless = true
# port = 7860
# enableCORS = false
# """)
# # Agents imports (keep same package you were using)
# from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
# from agents.tool import function_tool
# from agents.run import RunConfig

# # ---------------------------
# # Load environment variables
# # ---------------------------
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # ---------------------------
# # Context Management Class
# # ---------------------------
# class AgentContext:
#     @asynccontextmanager
#     async def create_agent():
#         """Context manager for agent resources"""
#         # Initialize if not in session state
#         if "agent_initialized" not in st.session_state:
#             st.session_state.provider = AsyncOpenAI(
#                 api_key=GEMINI_API_KEY,
#                 base_url="https://generativelanguage.googleapis.com/v1beta/openai"
#             )
            
#             st.session_state.model = OpenAIChatCompletionsModel(
#                 model="gemini-2.0-flash",
#                 openai_client=st.session_state.provider
#             )
#             st.session_state.config = RunConfig(
#                 model=st.session_state.model,
#                 model_provider=st.session_state.provider,
#                 tracing_disabled=True
#             )
            
#             # Tool definition remains the same
#             @function_tool("get_info")
#             def get_info() -> str:
#                 """
#                 Fetches profile data about Muhammad Daniyal from his personal API endpoint.
#                 Returns JSON string with his details or an error message.
#                 """
#                 try:
#                     resp = requests.get("https://my-api-navy-ten.vercel.app/", timeout=10)
#                     if resp.status_code == 200:
#                         # return raw text (agent instructions require using tool output directly)
#                         return resp.text
#                     else:
#                         return json.dumps({"error": f"Status code {resp.status_code}"})
#                 except Exception as e:
#                     return json.dumps({"error": str(e)})
            
#             st.session_state.agent = Agent(
#                 name="Personal Assistant Agent",
#                 instructions="""
#             You are an AI assistant for Muhammad Daniyal. Your main job is to respond to user queries
#             using accurate data from the provided API using the tool `get_info`. Follow the tool-calling
#             guidelines and hallucination control rules in the original specification: always call get_info
#             for personal details, don't fabricate missing info, and reply with the exact phrases required
#             for greetings/goodbyes. If something is missing say: "Sorry, this information is currently unavailable."
#                 """,
#                 model=st.session_state.model,
#                 tools=[get_info],
#             )
            
#             st.session_state.agent_initialized = True
        
#         # Yield the agent for use
#         try:
#             yield st.session_state.agent
#         finally:
#             # Cleanup is automatic due to session state persistence
#             pass

# # ---------------------------
# # Async Runner Function
# # ---------------------------
# async def run_agent_with_context(history):
#     """Run agent with proper context management"""
#     async with AgentContext.create_agent() as agent:
#         result = await Runner.run(agent, input=history, run_config=st.session_state.config)
#         return getattr(result, "final_output", None) or getattr(result, "output", None) or str(result)

# # ---------------------------
# # Streamlit UI
# # ---------------------------
# st.set_page_config(page_title="Personal Assistant", page_icon="🤖", layout="centered")
# st.markdown(
#     """
#     <h1 style="text-align: center;">Muhammad Daniyal's AI Assistant</h1>
#     """,
#     unsafe_allow_html=True
# )

# # Initialize session history (stateful)
# if "history" not in st.session_state:
#     st.session_state.history = [
#         {"role": "assistant", "content": "Hello and welcome! I'm the AI assistant of Muhammad Daniyal. Would you like to know more about him or explore something specific?"}
#     ]

# # Display chat messages
# for msg in st.session_state.history:
#     if msg["role"] == "assistant":
#         st.chat_message("assistant").write(msg["content"])
#     else:
#         st.chat_message("user").write(msg["content"])

# # User input field
# user_input = st.chat_input("Type your message here...")

# if user_input:
#     # Append and show user's message
#     st.session_state.history.append({"role": "user", "content": user_input})
#     st.chat_message("user").write(user_input)

#     # Process with proper context management
#     with st.spinner("Thinking..."):
#         # Ensure there's an event loop in this thread
#         try:
#             loop = asyncio.get_event_loop()
#             if loop.is_closed():
#                 raise RuntimeError("event loop closed")
#         except Exception:
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)

#         try:
#             # Run the agent with context management
#             response_text = loop.run_until_complete(run_agent_with_context(st.session_state.history))
            
#             # Append assistant response to history and display it
#             st.session_state.history.append({"role": "assistant", "content": response_text})
#             st.chat_message("assistant").write(response_text)
#         except Exception as e:
#             # Friendly error message in chat
#             err_text = f"Error running the agent: {type(e).__name__} - {str(e)}"
#             st.session_state.history.append({"role": "assistant", "content": err_text})
#             st.chat_message("assistant").write(err_text)

import os
import json
import requests
import asyncio
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter


import streamlit as st
os.makedirs(os.path.expanduser('~/.streamlit'), exist_ok=True)
with open(os.path.expanduser('~/.streamlit/config.toml'), 'w') as f:
    f.write("""
[server]
headless = true
port = 7860
enableCORS = false
""")
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
# Context Management Class
# ---------------------------
class AgentContext:
    @asynccontextmanager
    async def create_agent():
        """Context manager for agent resources"""
        # Initialize if not in session state
        if "agent_initialized" not in st.session_state:
            st.session_state.provider = AsyncOpenAI(
                api_key=GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai"
            )
            
            st.session_state.model = OpenAIChatCompletionsModel(
                model="gemini-2.0-flash",
                openai_client=st.session_state.provider
            )
            st.session_state.config = RunConfig(
                model=st.session_state.model,
                model_provider=st.session_state.provider,
                tracing_disabled=True
            )
            
            # Tool definition remains the same
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
            
            st.session_state.agent = Agent(
                name="Personal Assistant Agent",
                instructions=f"""
            You are an AI assistant for Muhammad Daniyal. You're speaking with {st.session_state.get('user_name', 'a user')}.
            Your main job is to respond to user queries using accurate data from the provided API using the tool `get_info`.
            Follow the tool-calling guidelines and hallucination control rules in the original specification: 
            always call get_info for personal details, don't fabricate missing info, and reply with the exact phrases required
            for greetings/goodbyes. If something is missing say: "Sorry, this information is currently unavailable."
                """,
                model=st.session_state.model,
                tools=[get_info],
            )
            
            st.session_state.agent_initialized = True
        
        # Yield the agent for use
        try:
            yield st.session_state.agent
        finally:
            # Cleanup is automatic due to session state persistence
            pass

# ---------------------------
# Async Runner Function
# ---------------------------
async def run_agent_with_context(history):
    """Run agent with proper context management"""
    async with AgentContext.create_agent() as agent:
        result = await Runner.run(agent, input=history, run_config=st.session_state.config)
        return getattr(result, "final_output", None) or getattr(result, "output", None) or str(result)

# ---------------------------
# Streamlit UI with shadcn-like styling
# ---------------------------

# Add custom CSS to mimic shadcn/ui styles
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* shadcn-like styles */
    .shadcn-card {
        font-family: 'Inter', sans-serif;
        background-color: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
    }
    
    .shadcn-card-header {
        margin-bottom: 1.5rem;
    }
    
    .shadcn-card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .shadcn-card-description {
        color: #64748b;
        font-size: 0.875rem;
    }
    
    /* Button styling */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        background-color: #18181b;
        color: white;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #27272a;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        font-family: 'Inter', sans-serif;
        border-radius: 0.375rem;
        border: 1px solid #e2e8f0;
        padding: 0.5rem;
    }
    
    /* Header bar with username */
    .user-header {
        padding: 0.75rem 1rem;
        background-color: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
    }
    
    .user-greeting {
        font-weight: 500;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Personal Assistant", page_icon="🤖", layout="centered")

# Initialize session state variables
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False

# Display the main title
st.markdown(
    """
    <h1 style="text-align: center; font-family: 'Inter', sans-serif; margin-bottom: 1.5rem;">
        Muhammad Daniyal's AI Assistant
    </h1>
    """,
    unsafe_allow_html=True
)

# Display user header if conversation has started
if st.session_state.conversation_started and st.session_state.user_name:
    st.markdown(
        f"""
        <div class="user-header">
            <span class="user-greeting">👋 Hello, {st.session_state.user_name}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Name input card (shadcn style)
if not st.session_state.conversation_started:
    st.markdown(
        """
        <div class="shadcn-card">
            <div class="shadcn-card-header">
                <h3 class="shadcn-card-title">Welcome</h3>
                <p class="shadcn-card-description">Please enter your name to start the conversation.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_name = st.text_input("Your Name", key="name_input", placeholder="Enter your name...")
        start_button = st.button("Start Conversation")
        
        if start_button and user_name:
            st.session_state.user_name = user_name
            st.session_state.conversation_started = True
            st.rerun()

# Initialize history only after user enters name
if st.session_state.conversation_started and "history" not in st.session_state:
    st.session_state.history = [
        {"role": "assistant", "content": f"Hello {st.session_state.user_name}! Welcome to Muhammad Daniyal's AI assistant. How can I help you today?"}
    ]

# Display chat interface after user enters name
if st.session_state.conversation_started:
    # Display chat messages
    for msg in st.session_state.history:
        if msg["role"] == "assistant":
            st.chat_message("assistant").write(msg["content"])
        else:
            st.chat_message("user").write(msg["content"])

    # User input field
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Append and show user's message
        st.session_state.history.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # Process with proper context management
        with st.spinner("Thinking..."):
            # Ensure there's an event loop in this thread
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("event loop closed")
            except Exception:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            try:
                # Run the agent with context management
                response_text = loop.run_until_complete(run_agent_with_context(st.session_state.history))
                
                # Append assistant response to history and display it
                st.session_state.history.append({"role": "assistant", "content": response_text})
                st.chat_message("assistant").write(response_text)
            except Exception as e:
                # Friendly error message in chat
                err_text = f"Error running the agent: {type(e).__name__} - {str(e)}"
                st.session_state.history.append({"role": "assistant", "content": err_text})
                st.chat_message("assistant").write(err_text)