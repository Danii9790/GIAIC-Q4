import streamlit as st
import asyncio
import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel , AsyncOpenAI
# from openai import AsyncOpenAI, OpenAI
from typing import Dict, List
from pinecone import Pinecone

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
VERCEL_WEBHOOK_URL = "https://giaic-q4.vercel.app/set-appointment"
TWILIO_FROM = "whatsapp:+14155238886"
PATIENT_NUMBER = "whatsapp:+923196560895"

# Gemini Model Setup
external_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=external_client)

# Pinecone RAG Setup
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "healthcare-embeddings"
    healthcare_index = pc.Index(index_name)

    # OpenAI client for embeddings
    embedding_client = external_client(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/"
    )

    PINECONE_AVAILABLE = True
    print(f"[OK] Pinecone connected to index: {index_name}")
except Exception as e:
    print(f"[WARNING] Pinecone connection failed: {e}")
    PINECONE_AVAILABLE = False
    healthcare_index = None
    embedding_client = None

# -------------------- Constants --------------------
SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID")
SANITY_DATASET = os.getenv("SANITY_DATASET")
SANITY_TOKEN = os.getenv("SANITY_TOKEN")
SANITY_API_URL = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2023-07-19/data/mutate/{SANITY_DATASET}"

# -------------------- Global Doctor Data --------------------
DOCTORS_DATA = {
    "Dr. Ahmed Khan": {
        "name": "Dr. Ahmed Khan",
        "specialty": "Cardiologist",
        "city": "Karachi",
        "location": "Karachi, Pakistan",
        "fee": "Rs 2000",
        "availability": {
            "Monday to Friday": {
                "Morning": "10:00 AM - 2:00 PM",
                "Evening": "7:00 PM - 10:00 PM"
            }
        },
        "can_book_appointment": True
    },
    "Dr. Khan": {
        "name": "Dr. Khan",
        "specialty": "Neurologist",
        "city": "Islamabad",
        "location": "Islamabad, Pakistan",
        "fee": "Rs 2500",
        "availability": {
            "Monday to Friday": {
                "Morning": "9:00 AM - 1:00 PM",
                "Evening": "6:00 PM - 9:00 PM"
            }
        },
        "can_book_appointment": True
    },
    "Dr. Sarah Ali": {
        "name": "Dr. Sarah Ali",
        "specialty": "Dermatologist",
        "city": "Lahore",
        "location": "Lahore, Pakistan",
        "fee": "Rs 1500",
        "availability": {
            "Monday to Friday": {
                "Morning": "9:00 AM - 1:00 PM",
                "Evening": "6:00 PM - 9:00 PM"
            }
        },
        "can_book_appointment": False
    }
}

# -------------------- Function Tools --------------------
@function_tool
def get_doctors() -> Dict:
    """Get all available doctors with their complete information."""
    print(f"[OK] Using {len(DOCTORS_DATA)} local doctors")
    return DOCTORS_DATA

@function_tool
def search_doctor(specialty: str = "", city: str = "") -> List[str]:
    """Search doctors by specialty and/or city."""
    doctors = get_doctors()
    results = []

    for name, info in doctors.items():
        # Filter by specialty
        if specialty and specialty.lower() not in info["specialty"].lower():
            continue
        # Filter by city
        if city and city.lower() not in info["city"].lower():
            continue

        booking_status = "✅ Bookable" if info["can_book_appointment"] else "ℹ️ Info only"
        result = f"{name} ({info['specialty']}, {info['city']}) - {info['fee']} [{booking_status}]"
        results.append(result)

    return results if results else [
        "Dr. Ahmed Khan (Cardiologist, Karachi) - Rs 2000 [✅ Bookable]",
        "Dr. Khan (Neurologist, Islamabad) - Rs 2500 [✅ Bookable]",
        "Dr. Sarah Ali (Dermatologist, Lahore) - Rs 1500 [ℹ️ Info only]"
    ]

@function_tool
def search_medical_information(query: str, top_k: int = 3) -> str:
    """Search for medical information using RAG."""
    if not PINECONE_AVAILABLE:
        return "Medical database is currently unavailable. Please consult a healthcare professional."

    try:
        print(f"[RAG] Searching medical information for: '{query}'")

        # Create embedding for the query
        query_embedding = embedding_client.embeddings.create(
            model="text-embedding-004",
            input=query
        ).data[0].embedding

        # Search Pinecone
        search_results = healthcare_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        if not search_results.get("matches"):
            return "No specific medical information found. Please consult a healthcare professional."

        # Format results
        result_text = f"🏥 **Medical Information: {query}**\n\n"
        for i, match in enumerate(search_results["matches"][:3], 1):
            source_file = match["metadata"].get("source_file", "Unknown")
            text = match["metadata"].get("text", "")[:150] + "..."
            score = match.get("score", 0)
            result_text += f"**{i}.** {source_file} (Relevance: {score:.1%})\n{text}\n\n"

        result_text += "💡 **Important:** This information is for educational purposes only. Always consult a qualified healthcare professional."
        return result_text

    except Exception as e:
        print(f"[ERROR] RAG search failed: {e}")
        return f"Error searching medical information: {str(e)}"

@function_tool
def analyze_symptoms(symptoms: str) -> str:
    """Analyze symptoms and provide recommendations."""
    if not PINECONE_AVAILABLE:
        return "Symptom analysis is currently unavailable. Please consult a healthcare professional."

    try:
        print(f"[RAG] Analyzing symptoms: '{symptoms}'")

        # Enhanced symptom query
        enhanced_query = f"symptoms diagnosis {symptoms} medical condition treatment"

        # Create embedding
        symptoms_embedding = embedding_client.embeddings.create(
            model="text-embedding-004",
            input=enhanced_query
        ).data[0].embedding

        # Search for relevant medical information
        search_results = healthcare_index.query(
            vector=symptoms_embedding,
            top_k=5,
            include_metadata=True
        )

        # Analyze and recommend
        symptom_analysis = f"🩺 **Symptom Analysis**\n\n"
        symptom_analysis += f"**Reported Symptoms:** {symptoms}\n\n"

        # Check for critical symptoms
        critical_keywords = ["chest pain", "difficulty breathing", "severe pain", "emergency"]
        if any(keyword in symptoms.lower() for keyword in critical_keywords):
            symptom_analysis += "⚠️ **IMMEDIATE MEDICAL ATTENTION REQUIRED**\n\n"
            symptom_analysis += "Your symptoms may indicate a serious medical condition. Please seek immediate medical attention or call emergency services.\n\n"

        # Provide doctor recommendations based on symptoms
        symptom_analysis += "**📋 Recommended Actions:**\n"
        symptoms_lower = symptoms.lower()

        if any(keyword in symptoms_lower for keyword in ["chest pain", "heart", "palpitation", "blood pressure"]):
            symptom_analysis += "• Consult Dr. Ahmed Khan (Cardiologist) - Heart conditions\n"
        elif any(keyword in symptoms_lower for keyword in ["headache", "migraine", "dizziness", "brain"]):
            symptom_analysis += "• Consult Dr. Khan (Neurologist) - Brain/Nervous system\n"
        elif any(keyword in symptoms_lower for keyword in ["skin", "rash", "acne", "dermatology"]):
            symptom_analysis += "• Consider Dr. Sarah Ali (Dermatologist) - Skin conditions\n"
        else:
            symptom_analysis += "• Consider consulting Dr. Ahmed Khan (Cardiologist) for general evaluation\n"
            symptom_analysis += "• Or Dr. Khan (Neurologist) if symptoms persist\n"

        symptom_analysis += "\n⚠️ **Medical Disclaimer:** This analysis is for informational purposes only. Please consult a qualified healthcare professional for proper diagnosis and treatment."
        return symptom_analysis

    except Exception as e:
        print(f"[ERROR] Symptom analysis failed: {e}")
        return f"Error analyzing symptoms: {str(e)}"

@function_tool
def save_appointment(patientName: str, email: str, doctorName: str, date: str, time: str) -> str:
    """Save appointment to Sanity database."""
    # Check if doctor can accept appointments
    allowed_doctors = ["Dr. Ahmed Khan", "Dr. Khan"]
    if doctorName not in allowed_doctors:
        return f"⛔ Appointments are only available for Dr. Ahmed Khan and Dr. Khan. For {doctorName}, please contact them directly."

    try:
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

        if response.status_code == 200:
            return f"✅ Appointment confirmed for {patientName} with {doctorName} on {date} at {time}."
        else:
            return "❌ Failed to save appointment. Please try again."
    except Exception as e:
        return f"❌ Error saving appointment: {str(e)}"

# -------------------- Main Agent --------------------
def create_healthcare_agent():
    """Main healthcare agent with all capabilities"""
    return Agent(
        name="Healthcare Assistant",
        instructions="""
You are a helpful Healthcare Assistant that can help patients with:
1. Finding doctors by specialty or location
2. Analyzing symptoms and providing medical information
3. Booking appointments with available doctors
4. Providing health information from our database

Your capabilities:
- Use get_doctors() to get complete doctor information
- Use search_doctor() to find doctors by specialty or location
- Use search_medical_information() to find medical information
- Use analyze_symptoms() to analyze patient symptoms
- Use save_appointment() to book appointments (only Dr. Ahmed Khan and Dr. Khan)

IMPORTANT RESTRICTIONS:
- Only Dr. Ahmed Khan (Cardiologist) and Dr. Khan (Neurologist) can book appointments
- Always include medical disclaimers for medical information
- For critical symptoms (chest pain, difficulty breathing), advise immediate medical attention
- Always prioritize patient safety

Be helpful, clear, and professional. If patients need appointments, collect their name, email, preferred doctor, date, and time.
""",
        model=model,
        tools=[get_doctors, search_doctor, search_medical_information, analyze_symptoms, save_appointment]
    )

# -------------------- Conversation Context --------------------
class ConversationContext:
    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_history(self) -> str:
        if not self.messages:
            return ""

        history = "Recent conversation:\n"
        for msg in self.messages[-3:]:  # Last 3 messages
            prefix = "You" if msg["role"] == "assistant" else "Patient"
            history += f"{prefix}: {msg['content']}\n"
        return history

# -------------------- Main Response Function --------------------
async def get_response(user_input: str, context: ConversationContext) -> str:
    """Main function to handle user queries"""
    try:
        # Create agent
        agent = create_healthcare_agent()

        # Add conversation history to prompt
        history = context.get_history()
        if history:
            user_input = f"{history}\n\nPatient: {user_input}"

        # Run the agent
        run_result = await Runner.run(agent, user_input)

        # Add messages to context
        context.add_message("user", user_input.split('\n')[-1])
        context.add_message("assistant", run_result.final_output)

        return run_result.final_output

    except Exception as e:
        print(f"[ERROR] Agent execution failed: {e}")
        return "I apologize, but I encountered an error. Please try again or contact support if the problem persists."

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Healthcare Assistant", page_icon="🏥")
st.title("🏥 AI Healthcare Assistant")

st.markdown("""
Welcome! I'm here to help you with:

🔍 **Find Doctors** - Search by specialty or location
🩺 **Symptom Analysis** - Understand your symptoms better
📅 **Book Appointments** - Schedule with available doctors
💊 **Medical Information** - Get health information from our database

*Dr. Ahmed Khan (Cardiologist) and Dr. Khan (Neurologist) are available for appointments*

⚠️ **Note:** Medical information is for educational purposes only. Always consult qualified healthcare professionals.
""")

# Initialize conversation context
if "context" not in st.session_state:
    st.session_state.context = ConversationContext()

if "history" not in st.session_state:
    st.session_state.history = []

# User input
user_input = st.chat_input("How can I help you today? (e.g., 'I have chest pain', 'Find a cardiologist', 'Book appointment')")

# Display chat history
for user_msg, assistant_msg in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(user_msg)
    with st.chat_message("assistant"):
        st.markdown(assistant_msg)

# Handle new user input
if user_input:
    st.session_state.history.append((user_input, "Thinking..."))
    st.rerun()

# Process the message
if st.session_state.history and st.session_state.history[-1][1] == "Thinking...":
    last_user_message = st.session_state.history[-1][0]

    with st.spinner("Processing your request..."):
        try:
            response = asyncio.run(get_response(last_user_message, st.session_state.context))
            st.session_state.history[-1] = (last_user_message, response)
        except Exception as e:
            print(f"Error in main processing: {e}")
            st.session_state.history[-1] = (last_user_message, "I apologize, but I encountered an error. Please try again.")

    st.rerun()