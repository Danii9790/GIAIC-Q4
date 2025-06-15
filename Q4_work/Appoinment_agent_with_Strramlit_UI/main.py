import streamlit as st
import os
import json
import asyncio
from dotenv import load_dotenv
from twilio.rest import Client
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Twilio Sandbox Setup
TWILIO_FROM = "whatsapp:+14155238886"
DOCTOR_WHATSAPP = "whatsapp:+923173762160"
PATIENT_WHATSAPP = "whatsapp:+923196560895"
twilio_client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

# Gemini API Setup
gemini_api_key = os.getenv("GEMINI_API_KEY")
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# Function Tool: Get available doctors
@function_tool
def get_doctors() -> dict:
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

# Function Tool: Notify doctor for confirmation
@function_tool
def send_doctor_request(patient_name: str, doctor_name: str, date: str, time: str) -> str:
    message = (
        f"📢 New Appointment Request:\n"
        f"Patient: {patient_name}\n"
        f"Doctor: {doctor_name}\n"
        f"Date: {date} at {time}\n\n"
        f"👉 Reply with 'confirm' to approve."
    )
    try:
        twilio_client.messages.create(
            from_=TWILIO_FROM,
            to=DOCTOR_WHATSAPP,
            body=message
        )
        return "✅ Request sent to doctor. Waiting for confirmation..."
    except Exception as e:
        return f"❌ Failed to send to doctor: {e}"

# Function Tool: Notify patient after confirmation
@function_tool
def confirm_and_notify_patient(patient_name: str, doctor_name: str, date: str, time: str) -> str:
    message = (
        f"✅ Hello {patient_name}, your appointment with {doctor_name} is confirmed for {date} at {time}."
    )
    try:
        twilio_client.messages.create(
            from_=TWILIO_FROM,
            to=PATIENT_WHATSAPP,
            body=message
        )
        save_to_json(patient_name, doctor_name, date, time)
        return "✅ Confirmation sent to patient and saved."
    except Exception as e:
        return f"❌ Error notifying patient: {e}"

# Save to JSON
def save_to_json(patient_name, doctor_name, date, time):
    file = "patient.json"
    record = {
        "patient": patient_name,
        "doctor": doctor_name,
        "date": date,
        "time": time
    }
    if os.path.exists(file):
        with open(file, "r") as f:
            existing = json.load(f)
    else:
        existing = []
    existing.append(record)
    with open(file, "w") as f:
        json.dump(existing, f, indent=2)

# Define the agent
agent = Agent(
    name="Appointment Agent",
    instructions="""
You are a helpful assistant for booking doctor appointments.

1. Use `get_doctors` to show doctors.
2. Ask user for patient name, doctor, date, and time.
3. Call `send_doctor_request` to notify doctor on WhatsApp.
4. Wait for doctor reply to confirm.
5. Then call `confirm_and_notify_patient` to notify the patient and save data.
6. Always guide the user step-by-step.
""",
    model=model,
    tools=[get_doctors, send_doctor_request, confirm_and_notify_patient]
)

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="DoctorBot", page_icon="🩺")
st.title("🩺 Doctor Appointment Assistant")
st.markdown("Chat with the assistant to book appointments and get WhatsApp confirmations!")

if "chat" not in st.session_state:
    st.session_state.chat = []

user_msg = st.text_input("🧑‍💬 You:", key="user_input")

if user_msg:
    st.session_state.chat.append({"role": "user", "content": user_msg})
    with st.spinner("💬 Assistant is typing..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(Runner.run(agent, input=st.session_state.chat))
        assistant_reply = result.final_output
        st.session_state.chat.append({"role": "assistant", "content": assistant_reply})
        st.markdown(f"🤖 **Bot:** {assistant_reply}")

# Show full chat
with st.expander("📜 Chat History"):
    for msg in st.session_state.chat:
        st.markdown(f"**{msg['role'].capitalize()}**: {msg['content']}")
