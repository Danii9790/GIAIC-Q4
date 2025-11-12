import streamlit as st
import asyncio
import os
import json
import requests
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from typing import Dict, List
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter


# Configure Streamlit
os.makedirs(os.path.expanduser('~/.streamlit'), exist_ok=True)
with open(os.path.expanduser('~/.streamlit/config.toml'), 'w') as f:
    f.write("""
[server]
headless = true
port = 7860
enableCORS = false
""")

# -------------------- Load Environment --------------------
load_dotenv()

# Twilio / Webhook constants
VERCEL_WEBHOOK_URL = "https://giaic-q4.vercel.app/set-appointment"  # Update this if needed
TWILIO_FROM = "whatsapp:+14155238886"
PATIENT_NUMBER = "whatsapp:+923196560895"  # Replace with dynamic value in production

# Gemini Model Setup
external_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=external_client)

# -------------------- Function Tools --------------------
SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID")
SANITY_DATASET = os.getenv("SANITY_DATASET")
SANITY_TOKEN = os.getenv("SANITY_TOKEN")
SANITY_API_URL = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2023-07-19/data/mutate/{SANITY_DATASET}"

# ✅ Save to Sanity
@function_tool
def save_appointment(patientName: str, email: str, doctorName: str, date: str, time: str) -> str:
    query = {
        "query": '*[_type == "appointment" && doctorName == $doctorName && date == $date && time == $time][0]',
        "params": {"doctorName": doctorName, "date": date, "time": time}
    }
    check = requests.post(
        f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2023-07-19/data/query/{SANITY_DATASET}",
        headers={"Authorization": f"Bearer {SANITY_TOKEN}"},
        json=query
    )
    if check.status_code == 200 and check.json().get("result"):
        return "⛔ Sorry, this time slot is already booked!"

    doc = {
        "mutations": [
            {"create": {
                "_type": "appointment",
                "patientName": patientName,
                "email": email,
                "doctorName": doctorName,
                "date": date,
                "time": time,
                "status": "pending"
            }}
        ]
    }
    response = requests.post(SANITY_API_URL, headers={"Authorization": f"Bearer {SANITY_TOKEN}"}, json=doc)
    return "✅ Appointment saved to Sanity." if response.status_code == 200 else "❌ Sanity save failed."

# 🧠 Doctor Data

@function_tool
def get_doctors() -> Dict:
    try:
        print("Attempting to load doctors dataset from Kaggle...")
        file_path = "doctors-in-pakistan-dataset.csv"
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "riyanmujahid/doctors-in-pakistan-dataset",
            file_path
        )

        print(f"Dataset loaded successfully with {len(df)} records")
        print(f"Available columns: {df.columns.tolist()}")

        doctors_data = {}

        # Convert the DataFrame to dictionary format
        for _, row in df.iterrows():
            name = row.get("Name", "Unknown Doctor")
            specialty = row.get("Specialization", "General")
            city = row.get("City", "Unknown")

            doctors_data[name] = {
                "specialty": specialty,
                "city": city,
                "availability": {
                    "Monday to Friday": {
                        "Morning": "10:00 AM - 2:00 PM",
                        "Evening": "7:00 PM - 10:00 PM"
                    }
                }
            }

        if not doctors_data:
            print("No valid doctor data found in dataset, using fallback...")
            raise Exception("No valid doctors in dataset")

        print(f"Successfully processed {len(doctors_data)} doctors")
        return doctors_data

    except Exception as e:
        print(f"Kaggle dataset failed: {str(e)}")
        print("Using fallback mock data...")

        # Fallback mock data
        fallback_doctors = {
            "Dr. Ahmed Khan": {
                "specialty": "Cardiologist",
                "city": "Karachi",
                "availability": {
                    "Monday to Friday": {
                        "Morning": "10:00 AM - 2:00 PM",
                        "Evening": "7:00 PM - 10:00 PM"
                    }
                }
            },
            "Dr. Sarah Ali": {
                "specialty": "Dermatologist",
                "city": "Lahore",
                "availability": {
                    "Monday to Friday": {
                        "Morning": "9:00 AM - 1:00 PM",
                        "Evening": "6:00 PM - 9:00 PM"
                    }
                }
            },
            "Dr. Muhammad Hassan": {
                "specialty": "General Physician",
                "city": "Islamabad",
                "availability": {
                    "Monday to Friday": {
                        "Morning": "8:00 AM - 12:00 PM",
                        "Evening": "5:00 PM - 9:00 PM"
                    }
                }
            },
            "Dr. Fatima Zahra": {
                "specialty": "Pediatrician",
                "city": "Karachi",
                "availability": {
                    "Monday to Friday": {
                        "Morning": "10:00 AM - 2:00 PM",
                        "Evening": "6:00 PM - 9:00 PM"
                    }
                }
            },
            "Dr. Omar Farooq": {
                "specialty": "Orthopedic Surgeon",
                "city": "Lahore",
                "availability": {
                    "Monday to Friday": {
                        "Morning": "11:00 AM - 3:00 PM",
                        "Evening": "7:00 PM - 10:00 PM"
                    }
                }
            }
        }

        print(f"Returning {len(fallback_doctors)} fallback doctors")
        return fallback_doctors

# Search Doctor's
@function_tool
def search_doctor(specialty: str = "", city: str = "") -> List[str]:
    try:
        print(f"Searching for doctors with specialty: '{specialty}' and city: '{city}'")
        file_path = "doctors-in-pakistan-dataset.csv"
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "riyanmujahid/doctors-in-pakistan-dataset",
            file_path
        )

        print(f"Dataset loaded with {len(df)} records")
        print(f"Available columns: {df.columns.tolist()}")

        # Check if required columns exist
        if "Name" not in df.columns:
            print("Name column not found, checking available columns...")
            print(f"Available columns: {df.columns.tolist()}")
            raise Exception("Name column not found in dataset")

        # Filter based on inputs
        original_count = len(df)

        if specialty:
            if "Specialization" in df.columns:
                df = df[df["Specialization"].str.contains(specialty, case=False, na=False)]
                print(f"Filtered by specialty '{specialty}': {len(df)} records remaining")
            else:
                print(f"Specialization column not found, available columns: {df.columns.tolist()}")

        if city:
            if "City" in df.columns:
                df = df[df["City"].str.contains(city, case=False, na=False)]
                print(f"Filtered by city '{city}': {len(df)} records remaining")
            else:
                print(f"City column not found, available columns: {df.columns.tolist()}")

        # Get doctor names
        doctor_names = df["Name"].tolist()[:10]  # return top 10 matches
        print(f"Returning {len(doctor_names)} doctor names")

        if not doctor_names:
            print("No doctors found matching criteria, using fallback data...")
            # Return fallback doctors if no matches found
            fallback_doctors = [
                "Dr. Ahmed Khan (Cardiologist, Karachi)",
                "Dr. Sarah Ali (Dermatologist, Lahore)",
                "Dr. Muhammad Hassan (General Physician, Islamabad)",
                "Dr. Fatima Zahra (Pediatrician, Karachi)",
                "Dr. Omar Farooq (Orthopedic Surgeon, Lahore)"
            ]
            return fallback_doctors[:10]

        return doctor_names

    except Exception as e:
        print(f"Search failed: {str(e)}")
        print("Using fallback doctor data...")

        # Return fallback doctors on error
        fallback_doctors = [
            "Dr. Ahmed Khan (Cardiologist, Karachi)",
            "Dr. Sarah Ali (Dermatologist, Lahore)",
            "Dr. Muhammad Hassan (General Physician, Islamabad)",
            "Dr. Fatima Zahra (Pediatrician, Karachi)",
            "Dr. Omar Farooq (Orthopedic Surgeon, Lahore)"
        ]
        return fallback_doctors[:10]


# 🕊️ Simulate WhatsApp to Doctor
@function_tool
def send_doctor_request(patient_name: str, doctor_name: str, date: str, time: str) -> str:
    payload = {"patient_name": patient_name, "doctor_name": doctor_name, "date": date, "time": time}
    try:
        response = requests.post(VERCEL_WEBHOOK_URL, headers={"Content-Type": "application/json"}, json=payload)
        return "✅ Doctor notified via webhook!" if response.status_code == 200 else f"❌ Webhook failed ({response.status_code})"
    except Exception as e:
        return f"❌ Webhook error: {str(e)}"

# ✅ Patient Confirmation (Local)
@function_tool
def confirm_patient(patient_name: str, doctor_name: str, date: str, time: str) -> str:
    try:
        file = "appointments.json"
        data = json.load(open(file)) if os.path.exists(file) else []
        for a in data:
            if a["doctor"] == doctor_name and a["date"] == date and a["time"] == time:
                return "❌ Doctor already booked at that time."
        data.append({"patient": patient_name, "doctor": doctor_name, "date": date, "time": time})
        with open(file, "w") as f: json.dump(data, f, indent=2)
        return f"✅ Appointment confirmed for {patient_name} with {doctor_name} on {date} at {time}."
    except Exception as e:
        return f"❌ Failed to confirm appointment: {e}"

# -------------------- Context Management --------------------
class ConversationContext:
    def __init__(self):
        self.conversations = []
        self.current_state = {}
    
    def add_message(self, role: str, content: str):
        self.conversations.append({"role": role, "content": content})
    
    def get_conversation_summary(self) -> str:
        if not self.conversations:
            return ""
        
        summary = "Here's our conversation history:\n\n"
        for msg in self.conversations:
            prefix = "You" if msg["role"] == "assistant" else "Patient"
            summary += f"{prefix}: {msg['content']}\n\n"
        
        return summary
    
    def update_state(self, key, value):
        self.current_state[key] = value
    
    def get_state(self):
        return self.current_state

# -------------------- Agent --------------------
def create_agent_with_context(context: ConversationContext = None):
    context_str = ""
    state = {}
    
    if context:
        context_str = context.get_conversation_summary()
        state = context.get_state()
    
    state_str = ""
    if state:
        state_str = "\n\nCurrent appointment information collected so far:\n"
        for key, value in state.items():
            state_str += f"- {key}: {value}\n"
    
    agent = Agent(
        name="Doctor Assistant",
        instructions=f"""
You are a reliable and intelligent Doctor Appointment Assistant.
Your job is to **help patients book appointments with available doctors**. Follow the exact thinking steps and tool order to ensure safe, error-free bookings.

{context_str}
{state_str}

========================
💡 Your Capabilities
========================
1. 🩺 **Doctor Info**
   - Use get_doctors to fetch doctors, their specialties, and schedules.
   - Only book appointments with valid doctors.
2. 📅 **Booking an Appointment**
   - Ask the user for these details **step by step**:
     - Patient's full name
     - Doctor's name (must exist in doctor list)
     - Appointment date (must match availability)
     - Appointment time (must be in time range)
   - Validate doctor name and schedule using get_doctors before confirming.
3. ✅ **After collecting all data:**
   - Step 1: Call send_doctor_request to notify the doctor (Webhook).
   - Step 2: Call save_appointment to save to Sanity (backend DB).
   - Step 3: Call confirm_patient to log it locally and simulate patient notification.
4. 📲 **WhatsApp Logic**
   - Do NOT send WhatsApp directly. Assume it is handled outside this agent for now.
   - Only simulate confirmation.
========================
🧠 How to Think Internally
========================
- If doctor name is unknown → use get_doctors.
- If time or day mismatch → explain and ask again.
- Always check and confirm doctor availability before saving.
- Use polite tone. Guide the user if they are missing info.
- Don't skip any tool in the appointment workflow.
========================
🔁 Return clear messages
========================
- ✅ "Appointment booked successfully."
- ⛔ "Doctor not available on that day."
- ❌ "Failed to save appointment to backend."
NEVER guess or hallucinate schedule info. Always call tools.

Remember details from previous messages. If a user has already provided information like their name, doctor preference, or date, don't ask for it again.
"""
        ,
        model=model,
        tools=[get_doctors, send_doctor_request, save_appointment, confirm_patient,search_doctor]
    )
    
    return agent

async def get_response(user_input: str, context: ConversationContext) -> str:
    # Create agent with updated context
    agent_with_context = create_agent_with_context(context)
    
    # Run the agent with the user input
    run_result = await Runner.run(agent_with_context, user_input)
    
    # Add messages to context
    context.add_message("user", user_input)
    context.add_message("assistant", run_result.final_output)
    
    # Try to extract appointment information from the conversation
    update_context_state(context, user_input, run_result.final_output)
    
    return run_result.final_output

def update_context_state(context: ConversationContext, user_input: str, agent_response: str):
    """Extract and update appointment information in the context state"""
    
    # Extract patient name
    if "name is" in user_input.lower() or "my name is" in user_input.lower():
        name_parts = user_input.split("is")
        if len(name_parts) > 1:
            name = name_parts[1].strip().split(".")[0].strip()
            context.update_state("patient_name", name)
    
    # Extract doctor name
    doctor_names = ["Dr. Khan", "Dr. Ahmed"]
    for doctor in doctor_names:
        if doctor in user_input or doctor in agent_response:
            context.update_state("doctor_name", doctor)
    
    # Extract date (simple pattern matching)
    date_indicators = ["on ", "for ", "date "]
    for indicator in date_indicators:
        if indicator in user_input.lower() and any(month in user_input for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
            parts = user_input.split(indicator)
            if len(parts) > 1:
                date_part = parts[1].split(".")[0].strip()
                # Simple date extraction - in a real app you'd use a more robust method
                if any(day in date_part for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                    context.update_state("date", date_part)
    
    # Extract time
    time_indicators = ["at ", "time "]
    for indicator in time_indicators:
        if indicator in user_input.lower() and ("AM" in user_input or "PM" in user_input):
            parts = user_input.split(indicator)
            if len(parts) > 1:
                time_part = parts[1].split(".")[0].strip()
                if "AM" in time_part or "PM" in time_part:
                    context.update_state("time", time_part)

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Doctor Appointment Assistant", page_icon="🩺")
st.title("🩺 Doctor Appointment Assistant")
st.markdown("This assistant helps you find a doctor and book an appointment via WhatsApp using Twilio.")

# Initialize conversation context if not exists
if "context" not in st.session_state:
    st.session_state.context = ConversationContext()

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Ask about doctor availability or book an appointment...")

# Display chat history
for user_msg, assistant_msg in st.session_state.history:
    with st.chat_message("user"): st.markdown(user_msg)
    with st.chat_message("assistant"): st.markdown(assistant_msg)

if user_input:
    st.session_state.history.append((user_input, "thinking..."))
    st.rerun()

if st.session_state.history and st.session_state.history[-1][1] == "thinking...":
    last_user_message = st.session_state.history[-1][0]
    with st.spinner("Thinking..."):
        response = asyncio.run(get_response(last_user_message, st.session_state.context))
    st.session_state.history[-1] = (last_user_message, response)
    st.rerun()