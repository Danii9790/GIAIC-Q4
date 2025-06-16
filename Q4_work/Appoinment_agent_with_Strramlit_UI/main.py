# import streamlit as st
# import os
# import json
# import asyncio
# from dotenv import load_dotenv
# from twilio.rest import Client
# from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
# from openai import AsyncOpenAI

# # Load environment variables
# load_dotenv()

# # Twilio Sandbox Setup
# TWILIO_FROM = "whatsapp:+14155238886"
# DOCTOR_WHATSAPP = "whatsapp:+923173762160"
# PATIENT_WHATSAPP = "whatsapp:+923196560895"
# twilio_client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

# # Gemini API Setup
# gemini_api_key = os.getenv("GEMINI_API_KEY")
# external_client = AsyncOpenAI(
#     api_key=gemini_api_key,
#     base_url="https://generativelanguage.googleapis.com/v1beta/"
# )
# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=external_client
# )

# # Function Tool: Get available doctors
# @function_tool
# def get_doctors() -> dict:
#     return {
#         "Dr. Khan": {
#             "specialty": "Dermatologist",
#             "availability": {
#                 "Tuesday": "12PM - 4PM",
#                 "Thursday": "10AM - 1PM"
#             }
#         },
#         "Dr. Ahmed": {
#             "specialty": "Neurologist",
#             "availability": {
#                 "Monday": "1PM - 5PM",
#                 "Friday": "10AM - 3PM"
#             }
#         }
#     }

# # Function Tool: Notify doctor for confirmation

# # @function_tool
# # def send_doctor_request(patient_name: str, doctor_name: str, date: str, time: str) -> str:
# #     message = (
# #         f"📢 New Appointment Request:\n"
# #         f"Patient: {patient_name}\n"
# #         f"Doctor: {doctor_name}\n"
# #         f"Date: {date} at {time}\n\n"
# #         f"👉 Reply with 'confirm' to approve."
# #     )
# #     try:
# #         twilio_client.messages.create(
# #             from_=TWILIO_FROM,
# #             to=DOCTOR_WHATSAPP,
# #             body=message
# #         )
# #         return "✅ Request sent to doctor. Waiting for confirmation..."
# #     except Exception as e:
# #         return f"❌ Failed to send to doctor: {e}"
# import requests

# @function_tool
# def send_doctor_request(patient_name: str, doctor_name: str, date: str, time: str) -> str:
#     try:
#         # POST appointment info to your webhook deployed on Vercel
#         response = requests.post(
#             "https://giaic-q4.vercel.app/set-appointment",
#             json={
#                 "patient_name": patient_name,
#                 "doctor_name": doctor_name,
#                 "date": date,
#                 "time": time
#             }
#         )

#         if response.status_code == 200:
#             return "✅ Appointment request sent to doctor. Awaiting doctor's confirmation..."
#         else:
#             return f"❌ Failed to send to webhook. Status code: {response.status_code}"
#     except Exception as e:
#         return f"❌ Error sending to webhook: {e}"

# # Function Tool: Notify patient after confirmation
# @function_tool
# def confirm_and_notify_patient(patient_name: str, doctor_name: str, date: str, time: str) -> str:
#     message = (
#         f"✅ Hello {patient_name}, your appointment with {doctor_name} is confirmed for {date} at {time}."
#     )
#     try:
#         twilio_client.messages.create(
#             from_=TWILIO_FROM,
#             to=PATIENT_WHATSAPP,
#             body=message
#         )
#         save_to_json(patient_name, doctor_name, date, time)
#         return "✅ Confirmation sent to patient and saved."
#     except Exception as e:
#         return f"❌ Error notifying patient: {e}"

# # Save to JSON
# def save_to_json(patient_name, doctor_name, date, time):
#     file = "patient.json"
#     record = {
#         "patient": patient_name,
#         "doctor": doctor_name,
#         "date": date,
#         "time": time
#     }
#     if os.path.exists(file):
#         with open(file, "r") as f:
#             existing = json.load(f)
#     else:
#         existing = []
#     existing.append(record)
#     with open(file, "w") as f:
#         json.dump(existing, f, indent=2)

# # Define the agent
# agent = Agent(
#     name="Appointment Agent",
#     instructions="""
# You are a helpful assistant for booking doctor appointments.

# 1. Use `get_doctors` to show doctors.
# 2. Ask user for patient name, doctor, date, and time.
# 3. Call `send_doctor_request` to notify doctor on WhatsApp.
# 4. Wait for doctor reply to confirm.
# 5. Then call `confirm_and_notify_patient` to notify the patient and save data.
# 6. Always guide the user step-by-step.
# """,
#     model=model,
#     tools=[get_doctors, send_doctor_request]
# )

# # ---------------- Streamlit UI ----------------
# st.set_page_config(page_title="DoctorBot", page_icon="🩺")
# st.title("🩺 Doctor Appointment Assistant")
# st.markdown("Chat with the assistant to book appointments and get WhatsApp confirmations!")

# if "chat" not in st.session_state:
#     st.session_state.chat = []

# user_msg = st.text_input("🧑‍💬 You:", key="user_input")

# if user_msg:
#     st.session_state.chat.append({"role": "user", "content": user_msg})
#     with st.spinner("💬 Assistant is typing..."):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         result = loop.run_until_complete(Runner.run(agent, input=st.session_state.chat))
#         assistant_reply = result.final_output
#         st.session_state.chat.append({"role": "assistant", "content": assistant_reply})
#         st.markdown(f"🤖 **Bot:** {assistant_reply}")

# # Show full chat
# with st.expander("📜 Chat History"):
#     for msg in st.session_state.chat:
#         st.markdown(f"**{msg['role'].capitalize()}**: {msg['content']}")


# import streamlit as st
# import os
# import json
# import asyncio
# import requests
# from dotenv import load_dotenv
# from twilio.rest import Client
# from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
# from openai import AsyncOpenAI

# # -------------------- Environment Setup --------------------
# load_dotenv()

# # Twilio Setup
# TWILIO_FROM = "whatsapp:+14155238886"
# twilio_client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

# # Gemini Model Setup
# gemini_api_key = os.getenv("GEMINI_API_KEY")
# external_client = AsyncOpenAI(
#     api_key=gemini_api_key,
#     base_url="https://generativelanguage.googleapis.com/v1beta/"
# )
# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=external_client
# )

# # -------------------- Function Tools --------------------

# @function_tool
# def get_doctors() -> dict:
#     """Returns available doctors with their specialties and timings."""
#     return {
#         "Dr. Khan": {
#             "specialty": "Dermatologist",
#             "availability": {
#                 "Tuesday": "12PM - 4PM",
#                 "Thursday": "10AM - 1PM"
#             }
#         },
#         "Dr. Ahmed": {
#             "specialty": "Neurologist",
#             "availability": {
#                 "Monday": "1PM - 5PM",
#                 "Friday": "10AM - 3PM"
#             }
#         }
#     }
# @function_tool
# def send_doctor_request(patient_name: str, doctor_name: str, date: str, time: str) -> str:
#     """Send appointment request to webhook for notifying the doctor."""
#     try:
#         payload = {
#             "patient_name": patient_name,
#             "doctor_name": doctor_name,
#             "date": date,
#             "time": time
#         }

#         response = requests.post(
#             "https://giaic-q4-6mrj97ox4-muhammad-daniyals-projects-496f954f.vercel.app/set-appointment",
#             headers={"Content-Type": "application/json"},
#             json=payload
#         )

#         if response.status_code == 200:
#             return "✅ Appointment request sent to doctor successfully. Waiting for their confirmation on WhatsApp..."
#         else:
#             return f"❌ Failed to send request. Server responded with status code {response.status_code}: {response.text}"
#     except Exception as e:
#         return f"❌ Error sending appointment request to webhook: {str(e)}"


# @function_tool
# def confirm_and_notify_patient(patient_name: str, doctor_name: str, date: str, time: str) -> str:
#     """Sends WhatsApp confirmation to the patient and logs it locally."""
#     try:
#         message = (
#             f"✅ Hello {patient_name}, your appointment with {doctor_name} is confirmed for {date} at {time}."
#         )
#         twilio_client.messages.create(
#             from_=TWILIO_FROM,
#             to="whatsapp:+923196560895",  # Replace with actual patient number
#             body=message
#         )
#         save_to_json(patient_name, doctor_name, date, time)
#         return "✅ Patient notified and appointment saved."
#     except Exception as e:
#         return f"❌ Failed to notify patient: {e}"

# def save_to_json(patient_name, doctor_name, date, time):
#     """Stores appointment data in local JSON file."""
#     record = {
#         "patient": patient_name,
#         "doctor": doctor_name,
#         "date": date,
#         "time": time
#     }
#     file = "appointments.json"
#     try:
#         if os.path.exists(file):
#             with open(file, "r") as f:
#                 data = json.load(f)
#         else:
#             data = []
#         data.append(record)
#         with open(file, "w") as f:
#             json.dump(data, f, indent=2)
#     except Exception as e:
#         print(f"Error saving JSON: {e}")

# # -------------------- Agent Setup --------------------
# agent = Agent(
#     name="DoctorBot",
#     instructions="""
# You are DoctorBot, a helpful and polite assistant that helps users book appointments with doctors via WhatsApp.

# Follow these steps strictly:

# 1. When the user starts, call `get_doctors` to show all available doctors and their timings.
# 2. Ask for:
#    - Patient's full name
#    - Desired doctor's name (match exactly from the list)
#    - Appointment date
#    - Preferred time
# 3. Call `send_doctor_request` to notify the doctor about the request via a webhook or vercel api.
# 4. Instruct the user to wait for confirmation from the doctor via WhatsApp. 
#    (This will be sent through an external system like Twilio or CallMeBot.)
# 5. Once the webhook confirms that the doctor approved, call `confirm_and_notify_patient`
#    to send a final WhatsApp confirmation to the patient.
# 6. Be clear, polite, and step-by-step in your replies. Avoid repeating the same tool unless needed.
# call the vercel api 

# Note: Try your best to help the user complete the appointment successfully, and always assume the WhatsApp confirmation is an important final step.
# """,
#     model=model,
#     tools=[get_doctors, send_doctor_request, confirm_and_notify_patient]
# )

# # -------------------- Streamlit UI --------------------

# st.set_page_config(page_title="DoctorBot", page_icon="🩺")
# st.title("🩺 Doctor Appointment Assistant")
# st.markdown("Use this assistant to book doctor appointments and get confirmations via WhatsApp.")

# if "chat" not in st.session_state:
#     st.session_state.chat = []

# user_msg = st.text_input("🧑‍💬 You:", key="user_input")

# if user_msg:
#     st.session_state.chat.append({"role": "user", "content": user_msg})
#     with st.spinner("🤖 DoctorBot is replying..."):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         result = loop.run_until_complete(Runner.run(agent, input=st.session_state.chat))
#         bot_reply = result.final_output
#         st.session_state.chat.append({"role": "assistant", "content": bot_reply})
#         st.markdown(f"**🤖 Bot:** {bot_reply}")

# # Show chat history
# with st.expander("📜 Chat History"):
#     for msg in st.session_state.chat:
#         role_icon = "🧑" if msg["role"] == "user" else "🤖"
#         st.markdown(f"**{role_icon} {msg['role'].capitalize()}**: {msg['content']}")


import streamlit as st
import os
import json
import asyncio
import requests
from dotenv import load_dotenv
from twilio.rest import Client
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

# -------------------- Environment Setup --------------------
load_dotenv()

# Twilio Setup
TWILIO_FROM = "whatsapp:+14155238886"
twilio_client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

# Gemini Model Setup
gemini_api_key = os.getenv("GEMINI_API_KEY")
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# -------------------- Function Tools --------------------

@function_tool
def get_doctors() -> dict:
    """Returns available doctors with their specialties and timings."""
    return {
        "Dr. Khan": {
            "specialty": "Dermatologist",
            "availability": {
                "Tuesday": "12PM - 4PM",
                "Thursday": "10AM - 1PM"
            }
        },
        "Dr. Ahmed": {
            "specialty": "Neurologist",
            "availability": {
                "Monday": "1PM - 5PM",
                "Friday": "10AM - 3PM"
            }
        }
    }

@function_tool
def send_doctor_request(patient_name: str, doctor_name: str, date: str, time: str) -> str:
    """Send appointment request to webhook for notifying the doctor."""
    try:
        payload = {
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "date": date,
            "time": time
        }

        response = requests.post(
            "https://giaic-q4.vercel.app/set-appointment",
            headers={"Content-Type": "application/json"},
            json=payload
        )

        if response.status_code == 200:
            return "✅ Appointment request sent to doctor successfully."
        else:
            return f"❌ Failed to send request. Status code {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Error sending request to webhook: {str(e)}"

@function_tool
def confirm_and_notify_patient(patient_name: str, doctor_name: str, date: str, time: str) -> str:
    """Sends WhatsApp confirmation to the patient and logs it locally."""
    try:
        message = (
            f"✅ Hello {patient_name}, your appointment with {doctor_name} is confirmed for {date} at {time}."
        )
        twilio_client.messages.create(
            from_=TWILIO_FROM,
            to="whatsapp:+923196560895",  # Replace with actual dynamic number if needed
            body=message
        )
        save_to_json(patient_name, doctor_name, date, time)
        return "✅ Patient notified and appointment saved."
    except Exception as e:
        return f"❌ Failed to notify patient: {e}"

def save_to_json(patient_name, doctor_name, date, time):
    """Stores appointment data in local JSON file."""
    record = {
        "patient": patient_name,
        "doctor": doctor_name,
        "date": date,
        "time": time
    }
    file = "appointments.json"
    try:
        if os.path.exists(file):
            with open(file, "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open(file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving JSON: {e}")

# -------------------- Sub Agents --------------------

info_collector_agent = Agent(
    name="InfoCollectorAgent",
    instructions="""
Collect the patient's full name, doctor's name, date, and time for appointment.
Ensure doctor exists from the list using `get_doctors`.
Return all data clearly as JSON with keys: patient_name, doctor_name, date, time.
""",
    model=model,
    tools=[get_doctors]
)

appointment_agent = Agent(
    name="AppointmentAgent",
    instructions="""
Take the collected info and:
1. Call `send_doctor_request` to notify doctor via webhook.
2. Then call `confirm_and_notify_patient` to send WhatsApp confirmation.
Return status after each step.
""",
    model=model,
    tools=[send_doctor_request, confirm_and_notify_patient]
)

# -------------------- Coordinator Agent --------------------

coordinator_agent = Agent(
    name="CoordinatorAgent",
    instructions="""
You are DoctorBot, the main coordinator.
First, hand off to InfoCollectorAgent to collect appointment details.
Then pass the data to AppointmentAgent to finalize the appointment and notify the patient.
""",
    model=model,
    handoffs=[info_collector_agent, appointment_agent]
)

# -------------------- Streamlit UI --------------------

st.set_page_config(page_title="DoctorBot", page_icon="🩺")
st.title("🩺 Doctor Appointment Assistant")
st.markdown("Use this assistant to book doctor appointments and get confirmations via WhatsApp.")

if "chat" not in st.session_state:
    st.session_state.chat = []

user_msg = st.text_input("🧑‍💬 You:", key="user_input")

if user_msg:
    st.session_state.chat.append({"role": "user", "content": user_msg})
    with st.spinner("🤖 DoctorBot is replying..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(Runner.run(coordinator_agent, input=st.session_state.chat))
        bot_reply = result.final_output
        st.session_state.chat.append({"role": "assistant", "content": bot_reply})
        st.markdown(f"**🤖 Bot:** {bot_reply}")

# Show chat history
with st.expander("📜 Chat History"):
    for msg in st.session_state.chat:
        role_icon = "🧑" if msg["role"] == "user" else "🤖"
        st.markdown(f"**{role_icon} {msg['role'].capitalize()}**: {msg['content']}")
