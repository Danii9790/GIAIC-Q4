import streamlit as st
import asyncio
import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel , AsyncOpenAI
from agents.run import RunConfig
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

# OpenAI Model Setup
external_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
model = OpenAIChatCompletionsModel(model="gpt-4o", openai_client=external_client)

config = RunConfig(
    tracing_disabled=True
)

# Pinecone RAG Setup
try:
    pc = Pinecone(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1"
    )
    index_name = "healthcare-embeddings"
    healthcare_index = pc.Index(index_name, host="https://healthcare-embeddings-locsd7i.svc.aped-4627-b74a.pinecone.io")

    # Create separate OpenAI client for embeddings
    embedding_client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
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
    print(f"[RAG_TOOL_CALL] search_medical_information() called with query: '{query}'")

    if not PINECONE_AVAILABLE:
        print(f"[RAG_WARNING] Pinecone not available, returning fallback message")
        return "Medical database is currently unavailable. Please consult a healthcare professional."

    try:
        print(f"[RAG] Creating embedding for query: '{query}'")

        # Create embedding for the query
        query_embedding = embedding_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding

        print(f"[RAG] Embedding created successfully (dimension: {len(query_embedding)})")

        # Search Pinecone
        print(f"[RAG] Searching Pinecone with top_k={top_k}")
        search_results = healthcare_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        print(f"[RAG] Pinecone search completed, found {len(search_results.get('matches', []))} matches")

        if not search_results.get("matches"):
            print(f"[RAG_WARNING] No matches found in Pinecone")
            return "No specific medical information found in our database. Please consult a healthcare professional."

        # Format results
        result_text = f"🏥 **Medical Information: {query}**\n\n"
        for i, match in enumerate(search_results["matches"][:3], 1):
            source_file = match["metadata"].get("source_file", "Unknown")
            text = match["metadata"].get("text", "")[:150] + "..."
            score = match.get("score", 0)
            result_text += f"**{i}.** {source_file} (Relevance: {score:.1%})\n{text}\n\n"
            print(f"[RAG] Match {i}: {source_file} (Score: {score:.4f})")

        result_text += "💡 **Important:** This information is for educational purposes only. Always consult a qualified healthcare professional."
        print(f"[RAG] Returning formatted response with {len(result_text)} characters")
        return result_text

    except Exception as e:
        print(f"[RAG_ERROR] RAG search failed: {e}")
        import traceback
        print(f"[RAG_ERROR] Traceback: {traceback.format_exc()}")
        return f"Error searching medical information: {str(e)}"

@function_tool
def analyze_symptoms(symptoms: str) -> str:
    """Analyze symptoms and provide recommendations."""
    print(f"[RAG_TOOL_CALL] analyze_symptoms() called with symptoms: '{symptoms}'")

    if not PINECONE_AVAILABLE:
        print(f"[RAG_WARNING] Pinecone not available for symptom analysis")
        return "Symptom analysis is currently unavailable. Please consult a healthcare professional."

    try:
        print(f"[RAG] Analyzing symptoms: '{symptoms}'")

        # Enhanced symptom query
        enhanced_query = f"symptoms diagnosis {symptoms} medical condition treatment"
        print(f"[RAG] Enhanced query: '{enhanced_query}'")

        # Create embedding
        symptoms_embedding = embedding_client.embeddings.create(
            model="text-embedding-3-small",
            input=enhanced_query
        ).data[0].embedding
        print(f"[RAG] Symptom embedding created successfully")

        # Search for relevant medical information
        print(f"[RAG] Searching Pinecone for symptom-related information")
        search_results = healthcare_index.query(
            vector=symptoms_embedding,
            top_k=5,
            include_metadata=True
        )

        matches_count = len(search_results.get("matches", []))
        print(f"[RAG] Found {matches_count} symptom-related matches in Pinecone")

        # Analyze and recommend
        symptom_analysis = f"🩺 **Symptom Analysis**\n\n"
        symptom_analysis += f"**Reported Symptoms:** {symptoms}\n\n"

        if matches_count > 0:
            symptom_analysis += f"**Database Analysis:** Found {matches_count} relevant medical records.\n\n"

        # Check for critical symptoms
        critical_keywords = ["chest pain", "difficulty breathing", "severe pain", "emergency"]
        if any(keyword in symptoms.lower() for keyword in critical_keywords):
            print(f"[RAG_CRITICAL] Critical symptoms detected: {symptoms}")
            symptom_analysis += "⚠️ **IMMEDIATE MEDICAL ATTENTION REQUIRED**\n\n"
            symptom_analysis += "Your symptoms may indicate a serious medical condition. Please seek immediate medical attention or call emergency services.\n\n"

        # Provide doctor recommendations based on symptoms
        symptom_analysis += "**📋 Recommended Actions:**\n"
        symptoms_lower = symptoms.lower()

        if any(keyword in symptoms_lower for keyword in ["chest pain", "heart", "palpitation", "blood pressure"]):
            symptom_analysis += "• Consult Dr. Ahmed Khan (Cardiologist) - Heart conditions\n"
            print(f"[RAG_RECOMMENDATION] Cardiologist recommended")
        elif any(keyword in symptoms_lower for keyword in ["headache", "migraine", "dizziness", "brain"]):
            symptom_analysis += "• Consult Dr. Khan (Neurologist) - Brain/Nervous system\n"
            print(f"[RAG_RECOMMENDATION] Neurologist recommended")
        elif any(keyword in symptoms_lower for keyword in ["skin", "rash", "acne", "dermatology"]):
            symptom_analysis += "• Consider Dr. Sarah Ali (Dermatologist) - Skin conditions\n"
            print(f"[RAG_RECOMMENDATION] Dermatologist recommended")
        else:
            symptom_analysis += "• Consider consulting Dr. Ahmed Khan (Cardiologist) for general evaluation\n"
            symptom_analysis += "• Or Dr. Khan (Neurologist) if symptoms persist\n"
            print(f"[RAG_RECOMMENDATION] General practitioner recommended")

        symptom_analysis += "\n⚠️ **Medical Disclaimer:** This analysis is for informational purposes only. Please consult a qualified healthcare professional for proper diagnosis and treatment."
        print(f"[RAG] Returning symptom analysis with {len(symptom_analysis)} characters")
        return symptom_analysis

    except Exception as e:
        print(f"[RAG_ERROR] Symptom analysis failed: {e}")
        import traceback
        print(f"[RAG_ERROR] Traceback: {traceback.format_exc()}")
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

# -------------------- Multi-Agent System --------------------
class AgentHandoff:
    """Handler for agent handoffs with context preservation"""
    def __init__(self, user_input: str, context: 'ConversationContext'):
        self.user_input = user_input
        self.context = context
        self.handoff_reason = ""

    def should_handoff_to_triage(self, user_input: str) -> bool:
        """Determine if input should go to triage agent"""
        triage_keywords = ["emergency", "urgent", "severe pain", "chest pain", "difficulty breathing", "bleeding"]
        return any(keyword in user_input.lower() for keyword in triage_keywords)

    def should_handoff_to_medical_info(self, user_input: str) -> bool:
        """Determine if input should go to medical info agent"""
        medical_keywords = ["what is", "tell me about", "information", "explain", "learn about", "medical info"]
        return any(keyword in user_input.lower() for keyword in medical_keywords)

    def should_handoff_to_symptom_analysis(self, user_input: str) -> bool:
        """Determine if input should go to symptom analysis agent"""
        symptom_keywords = [
            "symptom", "pain", "feeling", "diagnosis", "i have", "i'm experiencing", "hurts",
            "fever", "headache", "cough", "nausea", "sore throat", "fatigue", "weakness",
            "dizziness", "rash", "swelling", "breathing", "chest", "stomach", "back",
            "migraine", "vomiting", "diarrhea", "cold", "flu", "allergy", "burning",
            "numbness", "tingling", "stiffness", "cramps", "bloating"
        ]
        return any(keyword in user_input.lower() for keyword in symptom_keywords)

    def should_handoff_to_booking(self, user_input: str) -> bool:
        """Determine if input should go to booking agent"""
        booking_keywords = ["book", "appointment", "schedule", "reserve", "see doctor", "visit"]
        return any(keyword in user_input.lower() for keyword in booking_keywords)

def create_triage_agent():
    """Emergency triage agent for urgent situations"""
    return Agent(
        name="Emergency Triage",
        instructions="""
You are an Emergency Triage specialist. Your primary responsibility is to assess urgent medical situations.

EMERGENCY PROTOCOL:
1. Immediately identify any life-threatening symptoms
2. Provide clear, immediate guidance
3. Recommend emergency services when needed
4. Stay calm and professional

CRITICAL SYMPTOMS requiring IMMEDIATE attention:
- Chest pain or pressure
- Difficulty breathing
- Severe bleeding
- Loss of consciousness
- Severe head injury
- Stroke symptoms (facial drooping, arm weakness, speech difficulty)

For emergencies:
1. "CALL EMERGENCY SERVICES IMMEDIATELY [Emergency Number]"
2. "Do not wait - this requires immediate medical attention"
3. While waiting: provide basic safety guidance

Always end with: "This is an emergency assessment. If you're unsure, seek immediate medical help."

Use search_medical_information() only for non-urgent questions. Do not delay emergency guidance.
""",
        model=model,
        tools=[search_medical_information]
    )

def create_medical_info_agent():
    """Medical information specialist for health education"""
    return Agent(
        name="Medical Information Specialist",
        instructions="""
You are a Medical Information Specialist focused on providing accurate, educational health information.

YOUR PRIMARY RESPONSIBILITY: Always use search_medical_information() tool for any medical queries!

YOUR WORKFLOW:
1. For ANY medical question, first call search_medical_information() with the key terms
2. Use the retrieved information to craft your response
3. Add relevant context and explanations based on the search results
4. Include proper medical disclaimer

CAPABILITIES:
- search_medical_information(): Search our comprehensive medical database using RAG
- Provide evidence-based information with sources
- Include risk factors and prevention strategies

EXAMPLE USAGE:
- User asks "What is hypertension?" → Call search_medical_information("hypertension")
- User asks "diabetes symptoms" → Call search_medical_information("diabetes symptoms")
- User asks "heart disease prevention" → Call search_medical_information("heart disease prevention")

IMPORTANT:
- ALWAYS use search_medical_information() first - this is your primary tool
- Include the source information and relevance scores from search results
- Add medical disclaimer: "This information is educational. Consult healthcare professionals for personal medical advice."
- Never provide specific medical diagnoses
- Focus on general health education
- Recommend professional consultation for personal health issues

Format responses clearly with headings, bullet points, and source citations.
""",
        model=model,
        tools=[search_medical_information]
    )

def create_symptom_analysis_agent():
    """Symptom analysis specialist with RAG capabilities"""
    return Agent(
        name="Symptom Analysis Specialist",
        instructions="""
You are a Symptom Analysis Specialist trained to help patients understand their symptoms and guide them to appropriate care.

YOUR WORKFLOW:
1. ALWAYS call analyze_symptoms() first with the user's symptoms
2. For specific medical conditions mentioned, call search_medical_information() for detailed information
3. Use search_doctor() to find relevant specialists when needed
4. Provide urgency assessment and doctor recommendations

YOUR RESPONSIBILITIES:
- Provide comprehensive symptom analysis using our RAG database
- Assess urgency level (Emergency/Urgent/Non-urgent)
- Recommend appropriate medical specialists
- Use our medical knowledge base for evidence-based information

PRIMARY TOOLS:
1. analyze_symptoms(): Main symptom analysis with RAG search
2. search_medical_information(): Additional medical context for specific conditions
3. search_doctor(): Find specialists by specialty/location

URGENCY LEVELS:
🚨 EMERGENCY: Call emergency services immediately
⚡ URGENT: See doctor within 24 hours
📅 NON-URGENT: Schedule routine appointment

EXAMPLE USAGE:
- "chest pain" → call analyze_symptoms("chest pain")
- If heart disease mentioned → call search_medical_information("heart disease")
- Then call search_doctor("cardiologist") for recommendations

DOCTOR RECOMMENDATIONS:
- Heart-related symptoms → Dr. Ahmed Khan (Cardiologist)
- Neurological symptoms → Dr. Khan (Neurologist)
- Skin issues → Dr. Sarah Ali (Dermatologist) - information only

CRITICAL: Always use analyze_symptoms() first as your primary tool for any symptom-related queries.

Always end with proper medical disclaimer and recommendation to consult healthcare professionals.
""",
        model=model,
        tools=[analyze_symptoms, search_medical_information, search_doctor]
    )

def create_booking_agent():
    """Appointment booking specialist"""
    return Agent(
        name="Appointment Booking Specialist",
        instructions="""
You are an Appointment Booking Specialist focused on helping patients schedule medical appointments.

BOOKING PROCESS:
1. Confirm which doctor the patient wants to see
2. Collect required information (name, email, date, time)
3. Check doctor availability and booking restrictions
4. Confirm appointment details before saving

AVAILABLE DOCTORS:
✅ Dr. Ahmed Khan (Cardiologist, Karachi) - Rs 2000
✅ Dr. Khan (Neurologist, Islamabad) - Rs 2500
ℹ️ Dr. Sarah Ali (Dermatologist, Lahore) - Rs 1500 (Info only - no booking)

BOOKING RESTRICTIONS:
- Only Dr. Ahmed Khan and Dr. Khan accept online bookings
- Dr. Sarah Ali requires direct contact

TOOLS:
- Use get_doctors() to show complete doctor information
- Use search_doctor() to help patients find specialists
- Use save_appointment() to book appointments

BOOKING CONFIRMATION:
Always confirm: Patient Name, Email, Doctor, Date, Time before saving.
Provide clear confirmation message with appointment details.

If appointment fails, suggest the patient call the clinic directly.
""",
        model=model,
        tools=[get_doctors, search_doctor, save_appointment]
    )

def create_general_assistant_agent():
    """Main orchestrator agent that routes to specialists"""
    return Agent(
        name="Healthcare Assistant Coordinator",
        instructions="""
You are the main Healthcare Assistant Coordinator. Welcome patients and route them to the appropriate specialist.

YOUR CAPABILITIES:
- Basic medical information using our RAG database
- Doctor search and availability information
- General health guidance
- Intelligent routing to specialized agents

SPECIALISTS AVAILABLE:
🚨 Emergency Triage - For urgent medical situations
📚 Medical Information - For detailed health education and medical queries
🩺 Symptom Analysis - For comprehensive symptom evaluation and recommendations
📅 Appointment Booking - For scheduling with available doctors

YOUR TOOLS:
1. search_medical_information(): Search our comprehensive medical database for basic medical queries
2. get_doctors(): Show all available doctors and their information
3. search_doctor(): Find specialists by specialty or location

WHEN TO USE RAG:
For general medical questions that don't clearly require specialized attention:
- Basic health information queries
- General medical concepts
- Health education topics
- When routing to specialists isn't clearly needed

ROUTING LOGIC:
- Emergency symptoms (chest pain, difficulty breathing, severe pain) → Emergency Triage
- Specific medical condition queries ("What is X", "Tell me about Y") → Medical Information
- Symptom descriptions ("I have X", "fever, headache") → Symptom Analysis
- Booking requests ("book appointment", "schedule") → Appointment Booking
- General health questions → Use RAG to provide information, then suggest specialist if needed

WELCOME MESSAGE:
"Hello! I'm your AI Healthcare Assistant. I can help you with:
🚨 Emergency assessment for urgent situations
📚 Medical information and health education
🩺 Symptom analysis and doctor recommendations
📅 Appointment booking with our specialists

I have access to a comprehensive medical database and can provide evidence-based health information. How can I help you today?"

Be warm, professional, and helpful. Use search_medical_information() for relevant health queries, and suggest specialists when appropriate.
""",
        model=model,
        tools=[get_doctors, search_doctor, search_medical_information]  # Enhanced with RAG tool
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

# -------------------- Enhanced Multi-Agent Orchestrator --------------------
class MultiAgentOrchestrator:
    """Intelligent agent routing and handoff system with context preservation"""

    def __init__(self):
        self.general_agent = create_general_assistant_agent()
        self.triage_agent = create_triage_agent()
        self.medical_info_agent = create_medical_info_agent()
        self.symptom_agent = create_symptom_analysis_agent()
        self.booking_agent = create_booking_agent()
        self.handoff = AgentHandoff("", None)
        self.last_agent = None
        self.conversation_state = "initial"

    def analyze_conversation_context(self, user_input: str, context: ConversationContext) -> str:
        """Analyze conversation state for better routing"""
        if len(context.messages) > 0:
            last_assistant_msg = context.messages[-1].get("content", "").lower()

            # Context-aware handoff detection
            if "emergency" in last_assistant_msg or "urgent" in last_assistant_msg:
                return "follow_up_emergency"
            elif "appointment" in last_assistant_msg and "book" in user_input.lower():
                return "booking_followup"
            elif "symptom" in last_assistant_msg and "pain" in user_input.lower():
                return "symptom_followup"

        return "initial"

    def route_to_agent(self, user_input: str, context: ConversationContext) -> Agent:
        """Intelligently route user input to the appropriate agent with context awareness"""

        # Analyze conversation state
        self.conversation_state = self.analyze_conversation_context(user_input, context)

        # Priority 1: Emergency triage (highest priority)
        if self.handoff.should_handoff_to_triage(user_input):
            print(f"[ROUTING] Emergency detected → Triage Agent (State: {self.conversation_state})")
            self.last_agent = self.triage_agent
            return self.triage_agent

        # Priority 2: Symptom analysis
        if self.handoff.should_handoff_to_symptom_analysis(user_input):
            print(f"[ROUTING] Symptoms detected → Symptom Analysis Agent (State: {self.conversation_state})")
            self.last_agent = self.symptom_agent
            return self.symptom_agent

        # Priority 3: Medical information
        if self.handoff.should_handoff_to_medical_info(user_input):
            print(f"[ROUTING] Medical info query → Medical Information Agent (State: {self.conversation_state})")
            self.last_agent = self.medical_info_agent
            return self.medical_info_agent

        # Priority 4: Appointment booking
        if self.handoff.should_handoff_to_booking(user_input):
            print(f"[ROUTING] Booking request → Appointment Booking Agent (State: {self.conversation_state})")
            self.last_agent = self.booking_agent
            return self.booking_agent

        # Default: General assistant
        print(f"[ROUTING] General query → General Assistant Agent (State: {self.conversation_state})")
        self.last_agent = self.general_agent
        return self.general_agent

    def should_suggest_handoff(self, user_input: str, current_agent: Agent, context: ConversationContext) -> tuple[bool, str, Agent]:
        """Determine if we should suggest handing off to another agent"""

        # Check if user is asking for something different from current agent's scope
        user_lower = user_input.lower()

        # Emergency override - always prioritize
        if self.handoff.should_handoff_to_triage(user_input) and current_agent.name != "Emergency Triage":
            return True, "⚠️ **Emergency detected!** Connecting you to our Emergency Triage specialist...", self.triage_agent

        # Cross-agent handoffs based on user intent changes
        if current_agent.name == "Appointment Booking Specialist":
            if any(keyword in user_lower for keyword in ["what is", "tell me about", "information"]):
                return True, "📚 I see you're looking for medical information. Let me connect you with our Medical Information Specialist...", self.medical_info_agent

        elif current_agent.name == "Medical Information Specialist":
            if self.handoff.should_handoff_to_symptom_analysis(user_lower):
                return True, "🩺 I'd like to help you with those symptoms. Let me connect you to our Symptom Analysis Specialist...", self.symptom_agent

        elif current_agent.name == "Symptom Analysis Specialist":
            if self.handoff.should_handoff_to_booking(user_lower):
                return True, "📅 Based on your symptoms, it would be good to see a doctor. Let me connect you with our Appointment Booking Specialist...", self.booking_agent

        return False, "", current_agent

    def get_agent_context(self, agent: Agent, user_input: str, context: ConversationContext) -> str:
        """Get agent-specific context for better responses"""

        base_context = f"[SPECIALIST: {agent.name}]"

        # Add conversation state context
        if self.conversation_state != "initial":
            base_context += f" [CONVERSATION_STATE: {self.conversation_state}]"

        # Add previous agent context for handoffs
        if self.last_agent and self.last_agent.name != agent.name:
            base_context += f" [PREVIOUS_AGENT: {self.last_agent.name}]"

        # Add context from last messages
        if len(context.messages) > 1:
            last_topic = context.messages[-2].get("content", "")[:50]
            base_context += f" [PREVIOUS_TOPIC: {last_topic}]"

        return base_context

def create_healthcare_agent():
    """Create the main healthcare agent with routing"""
    orchestrator = MultiAgentOrchestrator()
    return orchestrator.general_agent

# -------------------- Enhanced Error Handling and Logging --------------------
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('healthcare_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HealthAgentError(Exception):
    """Custom exception for healthcare agent errors"""
    pass

class ErrorHandler:
    """Centralized error handling for the healthcare agent"""

    @staticmethod
    def handle_agent_error(e: Exception, context: str = "") -> str:
        """Handle agent-specific errors with user-friendly messages"""
        error_msg = str(e)
        logger.error(f"[AGENT_ERROR] {context}: {error_msg}")

        # Categorize errors and provide appropriate responses
        if "503" in error_msg or "overloaded" in error_msg.lower() or "model is overloaded" in error_msg.lower():
            return "⏳ **AI Service Busy:** The AI service is experiencing high demand. Please wait a moment and try again. For emergencies, contact emergency services immediately."
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            return "🔌 **Connection Issue:** I'm having trouble connecting to my services. Please try again in a moment."
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return "🔐 **Service Error:** There's an issue with service authentication. Please try again later."
        elif "pinecone" in error_msg.lower() or "database" in error_msg.lower():
            return "💾 **Database Issue:** Medical database is temporarily unavailable. General assistance is still available."
        elif "embedding" in error_msg.lower():
            return "🧠 **AI Processing Error:** I'm having trouble processing your request. Please rephrase and try again."
        else:
            return "🛠️ **System Error:** I encountered an unexpected error. Please try again or contact support."

    @staticmethod
    def log_agent_interaction(agent_name: str, user_input: str, response: str, execution_time: float = None):
        """Log agent interactions for monitoring and debugging"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "input_length": len(user_input),
            "response_length": len(response),
            "execution_time": execution_time
        }
        logger.info(f"[AGENT_INTERACTION] {log_data}")

    @staticmethod
    def validate_input(user_input: str) -> tuple[bool, str]:
        """Validate user input for safety and appropriateness"""
        if not user_input or not user_input.strip():
            return False, "Please provide a valid message."

        if len(user_input) > 2000:
            return False, "Your message is too long. Please keep it under 2000 characters."

        # Check for potentially harmful content (basic check)
        harmful_patterns = ["hack", "exploit", "malicious", "virus"]
        if any(pattern in user_input.lower() for pattern in harmful_patterns):
            logger.warning(f"[SUSPICIOUS_INPUT] {user_input[:100]}...")
            return False, "Your message contains inappropriate content. Please ask appropriate healthcare questions."

        return True, ""

    @staticmethod
    def get_fallback_response(user_input: str, agent_name: str) -> str:
        """Provide fallback responses when AI services are unavailable"""
        user_lower = user_input.lower()

        # Emergency keywords
        if any(keyword in user_lower for keyword in ["chest pain", "difficulty breathing", "emergency", "severe pain"]):
            return "🚨 **EMERGENCY SITUATION DETECTED**\n\nBased on your message, you may be experiencing a medical emergency. Please call emergency services immediately or go to the nearest emergency room.\n\n**Emergency Numbers:**\n- Pakistan: 1122\n- Local emergency services in your area\n\n**Do not wait** - seek immediate medical attention."

        # Symptom-related fallbacks
        if "fever" in user_lower:
            return "🩺 **About Fever**\n\nWhile I'm experiencing technical difficulties, here's some general information:\n\n**Fever Management:**\n- Rest and stay hydrated\n- Monitor temperature regularly\n- Over-the-counter fever reducers (consult pharmacist)\n- Seek medical attention if fever persists > 3 days or is very high\n\n**When to See a Doctor:**\n- Fever > 103°F (39.4°C)\n- Fever with severe headache, stiff neck, or rash\n- Difficulty breathing or chest pain\n\nPlease consult a healthcare professional for personalized advice."

        if "headache" in user_lower:
            return "🩺 **About Headaches**\n\nWhile I'm experiencing technical difficulties, here's some general information:\n\n**Headache Management:**\n- Rest in quiet, dark room\n- Stay hydrated\n- Over-the-counter pain relievers (if appropriate for you)\n- Avoid triggers like stress, lack of sleep\n\n**When to Seek Medical Attention:**\n- Sudden, severe headache\n- Headache with fever, stiff neck, confusion\n- Headache after head injury\n- Headaches that worsen or change pattern\n\nPlease consult Dr. Khan (Neurologist) for persistent or severe headaches."

        # Booking-related fallback
        if "book" in user_lower or "appointment" in user_lower:
            return "📅 **Appointment Booking**\n\nWhile I'm experiencing technical difficulties, here's how to book appointments:\n\n**Available Doctors:**\n- Dr. Ahmed Khan (Cardiologist, Karachi) - Rs 2000\n- Dr. Khan (Neurologist, Islamabad) - Rs 2500\n\n**Contact for Booking:**\n- Call the clinic directly\n- Use the hospital's online portal\n- Visit in person during working hours\n\nPlease try again later or contact the clinic directly for immediate booking."

        # Default fallback
        return f"⚠️ **Service Temporarily Unavailable**\n\nI'm experiencing technical difficulties with my AI services. This is a temporary issue.\n\n**For medical emergencies, please call emergency services immediately.**\n\n**For non-urgent matters:**\n- Please try again in a few minutes\n- Contact healthcare providers directly\n- Visit your nearest clinic\n\nI apologize for the inconvenience. Your health is important, so please don't delay seeking care if needed."

# -------------------- Enhanced Main Response Function --------------------
async def get_response(user_input: str, context: ConversationContext) -> str:
    """Main function to handle user queries with intelligent routing and error handling"""
    start_time = datetime.now()

    try:
        # Input validation
        is_valid, validation_msg = ErrorHandler.validate_input(user_input)
        if not is_valid:
            return validation_msg

        logger.info(f"[REQUEST] Processing: {user_input[:50]}...")

        # Initialize orchestrator
        orchestrator = MultiAgentOrchestrator()
        orchestrator.handoff.context = context
        orchestrator.handoff.user_input = user_input

        # Route to appropriate agent
        selected_agent = orchestrator.route_to_agent(user_input, context)

        # Add conversation history to prompt
        history = context.get_history()
        enhanced_input = user_input
        if history:
            enhanced_input = f"{history}\n\nPatient: {user_input}"

        # Add enhanced agent context
        agent_context = orchestrator.get_agent_context(selected_agent, user_input, context)
        enhanced_input = f"{agent_context} {enhanced_input}"

        logger.info(f"[ROUTING] Using agent: {selected_agent.name}")

        # Run the selected agent with timeout
        try:
            run_result = await Runner.run(selected_agent, enhanced_input, run_config=config)
        except asyncio.TimeoutError:
            logger.error(f"[TIMEOUT] Agent {selected_agent.name} timed out")
            return "⏰ **Timeout:** The request took too long to process. Please try again with a simpler question."
        except Exception as agent_error:
            logger.error(f"[AGENT_EXECUTION_ERROR] {selected_agent.name}: {str(agent_error)}")

            # Check if it's a 503/overload error and provide fallback
            error_msg = str(agent_error)
            if "503" in error_msg or "overloaded" in error_msg.lower() or "model is overloaded" in error_msg.lower():
                logger.info(f"[FALLBACK] Using fallback response for {selected_agent.name}")
                return ErrorHandler.get_fallback_response(user_input, selected_agent.name)

            return ErrorHandler.handle_agent_error(agent_error, f"Agent {selected_agent.name}")

        # Add messages to context
        context.add_message("user", user_input)
        context.add_message("assistant", run_result.final_output)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Log interaction
        ErrorHandler.log_agent_interaction(
            selected_agent.name,
            user_input,
            run_result.final_output,
            execution_time
        )

        logger.info(f"[SUCCESS] Response generated in {execution_time:.2f}s")
        return run_result.final_output

    except HealthAgentError as he:
        logger.error(f"[HEALTH_AGENT_ERROR] {str(he)}")
        return ErrorHandler.handle_agent_error(he, "HealthAgent specific error")
    except Exception as e:
        logger.error(f"[UNEXPECTED_ERROR] {type(e).__name__}: {str(e)}")
        return ErrorHandler.handle_agent_error(e, "Unexpected error")

# -------------------- Health Check Function --------------------
def system_health_check() -> Dict:
    """Perform health check on all system components"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "components": {}
    }

    # Check Pinecone
    try:
        if PINECONE_AVAILABLE and healthcare_index:
            # Test query
            healthcare_index.query(vector=[0.0]*768, top_k=1)
            health_status["components"]["pinecone"] = "healthy"
        else:
            health_status["components"]["pinecone"] = "disabled"
    except Exception as e:
        health_status["components"]["pinecone"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check OpenAI API
    try:
        external_client.models.list()
        health_status["components"]["openai"] = "healthy"
    except Exception as e:
        health_status["components"]["openai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Sanity
    try:
        if SANITY_TOKEN and SANITY_PROJECT_ID:
            health_status["components"]["sanity"] = "healthy"
        else:
            health_status["components"]["sanity"] = "missing_config"
    except Exception as e:
        health_status["components"]["sanity"] = f"error: {str(e)}"

    return health_status

# -------------------- Enhanced Streamlit UI --------------------
st.set_page_config(
    page_title="AI Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .feature-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        transition: transform 0.2s;
    }

    .feature-card:hover {
        transform: translateX(5px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .emergency-banner {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }

    .doctor-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
    }

    .stChatMessage {
        border-radius: 15px;
    }

    .quick-action-btn {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        margin: 0.25rem;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s;
    }

    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🏥 AI Healthcare Assistant</h1>
    <p>Your intelligent companion for better health management</p>
    <p><strong>Available 24/7 • Confidential • Professional</strong></p>
</div>
""", unsafe_allow_html=True)

# Emergency Banner
st.markdown("""
<div class="emergency-banner">
    🚨 <strong>EMERGENCY?</strong> For life-threatening situations, call emergency services immediately!
</div>
""", unsafe_allow_html=True)

# Sidebar with quick actions and doctor info
with st.sidebar:
    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🩺 Check Symptoms", help="Analyze your symptoms"):
            st.session_state.quick_action = "symptoms"
    with col2:
        if st.button("📅 Book Appointment", help="Schedule a doctor visit"):
            st.session_state.quick_action = "booking"

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Find Doctor", help="Search by specialty"):
            st.session_state.quick_action = "find_doctor"
    with col2:
        if st.button("💊 Medical Info", help="Health information"):
            st.session_state.quick_action = "info"

    st.markdown("---")

    st.markdown("### 👨‍⚕️ Available Doctors")

    doctors_info = DOCTORS_DATA
    for name, info in doctors_info.items():
        availability = "✅ Available" if info["can_book_appointment"] else "ℹ️ Info only"
        st.markdown(f"""
        <div class="doctor-card">
            <strong>{info['name']}</strong><br>
            {info['specialty']} • {info['city']}<br>
            Fee: {info['fee']}<br>
            Status: {availability}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📊 System Status")
    pinecone_status = "🟢 Connected" if PINECONE_AVAILABLE else "🔴 Disconnected"
    st.metric("Database", pinecone_status)
    st.metric("Available Doctors", len([d for d in doctors_info.values() if d["can_book_appointment"]]))

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Conversation")

    # Initialize conversation context
    if "context" not in st.session_state:
        st.session_state.context = ConversationContext()

    if "history" not in st.session_state:
        st.session_state.history = []

    # Quick action suggestions
    if "quick_action" in st.session_state:
        action_prompts = {
            "symptoms": "I'm experiencing some symptoms and need help understanding them.",
            "booking": "I'd like to book an appointment with a doctor.",
            "find_doctor": "I need to find a specialist for my condition.",
            "info": "I'd like to learn about a medical condition."
        }

        if st.session_state.quick_action in action_prompts:
            suggested_prompt = action_prompts[st.session_state.quick_action]
            st.markdown(f"💡 **Suggested:** {suggested_prompt}")
            if st.button("Use this prompt", key="use_prompt"):
                st.session_state.suggested_input = suggested_prompt

        del st.session_state.quick_action

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, (user_msg, assistant_msg) in enumerate(st.session_state.history):
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_msg)
            with st.chat_message("assistant", avatar="🏥"):
                st.markdown(assistant_msg)

    # Enhanced input area
    st.markdown("### 📝 How can I help you?")

    # Predefined suggestions
    suggestion_cols = st.columns(4)
    suggestions = [
        ("🩺 Check symptoms", "I have chest pain"),
        ("📅 Book appointment", "Book appointment"),
        ("🔍 Find specialist", "Find cardiologist"),
        ("💊 Health info", "What is hypertension")
    ]

    for i, (label, prompt) in enumerate(suggestions):
        with suggestion_cols[i]:
            if st.button(label, key=f"suggestion_{i}"):
                st.session_state.suggested_input = prompt

    # User input with suggestions
    if "suggested_input" in st.session_state:
        # Display the suggested prompt
        st.markdown(f"💡 **Suggested prompt:** `{st.session_state.suggested_input}`")
        col_send, col_cancel = st.columns([1, 3])
        with col_send:
            if st.button("📤 Send Suggestion", key="send_suggestion", help="Send this message"):
                st.session_state.message_to_send = st.session_state.suggested_input
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_suggestion", help="Cancel this suggestion"):
                del st.session_state.suggested_input

    # Check if we have a message to send
    if "message_to_send" in st.session_state:
        user_input = st.session_state.message_to_send
        del st.session_state.message_to_send
        if "suggested_input" in st.session_state:
            del st.session_state.suggested_input
    else:
        # Regular chat input
        user_input = st.chat_input("Type your message here...")

with col2:
    st.markdown("### 🎯 Services")

    services = [
        {
            "icon": "🚨",
            "title": "Emergency Triage",
            "description": "Immediate assessment for urgent medical situations"
        },
        {
            "icon": "🩺",
            "title": "Symptom Analysis",
            "description": "AI-powered symptom evaluation and recommendations"
        },
        {
            "icon": "📚",
            "title": "Medical Information",
            "description": "Reliable health information from our database"
        },
        {
            "icon": "📅",
            "title": "Appointment Booking",
            "description": "Schedule visits with available specialists"
        },
        {
            "icon": "🔍",
            "title": "Doctor Search",
            "description": "Find healthcare providers by specialty/location"
        },
        {
            "icon": "💊",
            "title": "Health Education",
            "description": "Learn about conditions, treatments, and prevention"
        }
    ]

    for service in services:
        st.markdown(f"""
        <div class="feature-card">
            <h4>{service['icon']} {service['title']}</h4>
            <p>{service['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### ⚠️ Important Notice")
    st.warning("""
    **Medical Disclaimer:** This AI assistant provides educational information only.
    Always consult qualified healthcare professionals for personal medical advice,
    diagnosis, or treatment.
    """)

# Handle new user input
if user_input:
    st.session_state.history.append((user_input, "🤔 Thinking..."))
    st.rerun()

# Process the message
if st.session_state.history and st.session_state.history[-1][1] == "🤔 Thinking...":
    last_user_message = st.session_state.history[-1][0]

    # Show processing status
    with st.spinner("🏥 Processing your request with AI..."):
        try:
            response = asyncio.run(get_response(last_user_message, st.session_state.context))
            st.session_state.history[-1] = (last_user_message, response)
        except Exception as e:
            print(f"Error in main processing: {e}")
            st.session_state.history[-1] = (last_user_message,
                "I apologize, but I encountered an error. Please try again or contact support if the problem persists.")

    st.rerun()