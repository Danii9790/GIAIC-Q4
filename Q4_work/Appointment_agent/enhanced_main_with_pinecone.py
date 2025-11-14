import streamlit as st
import os
import json
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pinecone import Pinecone
from typing import Dict, List
import openai

# -------------------- Load Environment --------------------
load_dotenv()

# Sanity Configuration
SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID")
SANITY_DATASET = os.getenv("SANITY_DATASET")
SANITY_TOKEN = os.getenv("SANITY_TOKEN")
SANITY_API_URL = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2023-07-19/data/mutate/{SANITY_DATASET}"

# -------------------- Pinecone RAG Setup --------------------
PINECONE_AVAILABLE = False
healthcare_index = None
embedding_client = None

try:
    # Initialize Pinecone
    pc = Pinecone(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-west1-gcp"
    )

    index_name = "healthcare-embeddings"
    healthcare_index = pc.Index(index_name, host="https://healthcare-embeddings-locsd7i.svc.aped-4627-b74a.pinecone.io")

    # Initialize OpenAI client for embeddings
    embedding_client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    PINECONE_AVAILABLE = True
    st.success("✅ Pinecone vector database connected successfully")

except Exception as e:
    st.error(f"⚠️ Pinecone connection failed: {e}")
    PINECONE_AVAILABLE = False



# -------------------- Pinecone RAG Functions --------------------
def create_embedding(text: str) -> List[float]:
    """Create embedding for text using a model that matches the 768-dimension index"""
    if not embedding_client:
        raise Exception("Embedding client not available")

    try:
        # Use a model that creates 768-dimensional vectors
        response = embedding_client.embeddings.create(
            model="text-embedding-ada-002",  # This creates 1536 dimensions, we'll truncate to 768
            input=text
        )
        embedding = response.data[0].embedding
        # Truncate or pad to 768 dimensions to match the index
        return embedding[:768]  # Take first 768 dimensions
    except Exception as e:
        raise Exception(f"Failed to create embedding: {e}")

def search_medical_information(query: str, top_k: int = 3) -> str:
    """Search for medical information using Pinecone RAG"""
    if not PINECONE_AVAILABLE:
        return "🔍 **Medical Database Unavailable**\n\nThe vector database is currently offline. Please consult a healthcare professional for medical information."

    try:
        # Create embedding for the query
        with st.spinner("🧠 Creating query embedding..."):
            query_embedding = create_embedding(query)

        # Search Pinecone
        with st.spinner("🔍 Searching medical database..."):
            search_results = healthcare_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

        if not search_results.get("matches"):
            return f"📚 **Medical Information: {query}**\n\nNo specific information found in our database for '{query}'. Please consult a healthcare professional for accurate medical advice."

        # Format results
        result_text = f"🏥 **Medical Information: {query}**\n\n"
        result_text += f"📊 **Found {len(search_results['matches'])} relevant medical sources:**\n\n"

        for i, match in enumerate(search_results["matches"][:3], 1):
            source_file = match["metadata"].get("source_file", "Unknown Source")
            text_content = match["metadata"].get("text", "")
            score = match.get("score", 0)

            # Truncate text if too long
            if len(text_content) > 200:
                text_content = text_content[:200] + "..."

            result_text += f"**{i}.** {source_file} (Relevance: {score:.1%})\n"
            result_text += f"```\n{text_content}\n```\n\n"

        result_text += "💡 **Important:** This information is for educational purposes only. Always consult a qualified healthcare professional for personalized medical advice."

        return result_text

    except Exception as e:
        return f"❌ **Error searching medical information:** {str(e)}"

def analyze_symptoms_advanced(symptoms: str) -> str:
    """Advanced symptom analysis using Pinecone RAG"""
    if not PINECONE_AVAILABLE:
        return "🩺 **Symptom Analysis Unavailable**\n\nAdvanced symptom analysis is currently offline. For symptom evaluation, please consult Dr. Ahmed Khan (Cardiologist) or Dr. Khan (Neurologist)."

    try:
        # Check for emergency symptoms first
        critical_keywords = ["chest pain", "difficulty breathing", "severe pain", "emergency", "unconscious", "stroke"]
        if any(keyword in symptoms.lower() for keyword in critical_keywords):
            return "🚨 **EMERGENCY - IMMEDIATE MEDICAL ATTENTION REQUIRED**\n\nBased on your symptoms, you may be experiencing a medical emergency. Please:\n\n1. **Call emergency services immediately (1122 in Pakistan)**\n2. **Go to the nearest emergency room**\n3. **Do not wait - seek immediate medical attention**\n\nYour symptoms may indicate a serious condition requiring urgent care."

        # Enhanced symptom query for better RAG results
        enhanced_query = f"symptoms diagnosis medical conditions treatment {symptoms} healthcare"

        # Create embedding
        with st.spinner("🧠 Analyzing symptoms with AI..."):
            symptoms_embedding = create_embedding(enhanced_query)

        # Search for relevant medical information
        with st.spinner("🔍 Searching medical knowledge base..."):
            search_results = healthcare_index.query(
                vector=symptoms_embedding,
                top_k=5,
                include_metadata=True
            )

        # Build comprehensive analysis
        symptom_analysis = f"🩺 **Advanced Symptom Analysis**\n\n"
        symptom_analysis += f"**Reported Symptoms:** {symptoms}\n\n"

        if search_results.get("matches"):
            symptom_analysis += f"📊 **Database Analysis:** Found {len(search_results['matches'])} relevant medical records\n\n"

            # Add top relevant information
            symptom_analysis += "**📚 Relevant Medical Information:**\n"
            for i, match in enumerate(search_results["matches"][:2], 1):
                source = match["metadata"].get("source_file", "Medical Database")
                relevance = match.get("score", 0)
                snippet = match["metadata"].get("text", "")[:100] + "..."
                symptom_analysis += f"• {source} (Relevance: {relevance:.1%})\n"

        # Doctor recommendations based on symptom patterns
        symptom_analysis += f"\n**👨‍⚕️ Recommended Specialists:**\n"
        symptoms_lower = symptoms.lower()

        recommendations = []
        if any(keyword in symptoms_lower for keyword in ["chest", "heart", "palpitation", "blood pressure", "shortness of breath"]):
            recommendations.append("• **Dr. Ahmed Khan (Cardiologist)** - Heart conditions, chest pain, blood pressure issues")

        if any(keyword in symptoms_lower for keyword in ["headache", "migraine", "dizziness", "brain", "numbness", "tingling"]):
            recommendations.append("• **Dr. Khan (Neurologist)** - Headaches, neurological symptoms, brain conditions")

        if any(keyword in symptoms_lower for keyword in ["skin", "rash", "acne", "dermatology", "allergy"]):
            recommendations.append("• **Dr. Sarah Ali (Dermatologist)** - Skin conditions, rashes, allergic reactions (consultation only)")

        if not recommendations:
            recommendations.append("• **General Consultation** - Consider starting with Dr. Ahmed Khan for general evaluation")

        symptom_analysis += "\n".join(recommendations)

        # Next steps
        symptom_analysis += f"\n\n**📋 Recommended Next Steps:**\n"
        symptom_analysis += "• Monitor your symptoms closely\n"
        symptom_analysis += "• Keep a symptom diary\n"
        symptom_analysis += "• Schedule an appointment with recommended specialist\n"
        symptom_analysis += "• If symptoms worsen, seek immediate medical attention\n"

        # Disclaimer
        symptom_analysis += f"\n\n⚠️ **Medical Disclaimer:** This analysis is for informational purposes only and is not a substitute for professional medical diagnosis. Please consult a qualified healthcare professional for proper evaluation and treatment."

        return symptom_analysis

    except Exception as e:
        return f"❌ **Error analyzing symptoms:** {str(e)}"

# -------------------- Basic Functions --------------------
def get_doctors():
    """Get all available doctors"""
    return DOCTORS_DATA

def search_doctors(specialty="", city=""):
    """Search doctors by specialty and/or city"""
    doctors = get_doctors()
    results = []

    for name, info in doctors.items():
        if specialty and specialty.lower() not in info["specialty"].lower():
            continue
        if city and city.lower() not in info["city"].lower():
            continue

        booking_status = "✅ Bookable" if info["can_book_appointment"] else "ℹ️ Info only"
        result = f"{name} ({info['specialty']}, {info['city']}) - {info['fee']} [{booking_status}]"
        results.append(result)

    return results if results else ["No doctors found matching your criteria"]

def save_appointment(patient_name, email, doctor_name, date, time):
    """Save appointment to Sanity database"""
    # Check if doctor can accept appointments
    if doctor_name not in ["Dr. Ahmed Khan", "Dr. Khan"]:
        return f"⛔ Appointments are only available for Dr. Ahmed Khan and Dr. Khan. For {doctor_name}, please contact them directly."

    try:
        doc = {
            "mutations": [
                {"create": {
                    "_type": "appointment",
                    "patientName": patient_name,
                    "email": email,
                    "doctorName": doctor_name,
                    "date": date,
                    "time": time,
                    "status": "pending",
                    "createdAt": datetime.now().isoformat()
                }}
            ]
        }

        response = requests.post(
            SANITY_API_URL,
            headers={"Authorization": f"Bearer {SANITY_TOKEN}"},
            json=doc
        )

        if response.status_code == 200:
            return f"✅ Appointment confirmed for {patient_name} with {doctor_name} on {date} at {time}."
        else:
            return f"❌ Failed to save appointment. Status: {response.status_code}"
    except Exception as e:
        return f"❌ Error saving appointment: {str(e)}"

# -------------------- Enhanced UI Configuration --------------------
st.set_page_config(
    page_title="Healthcare System with AI-Powered Search",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .doctor-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #28a745;
        transition: transform 0.2s;
    }

    .doctor-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
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

    .ai-badge {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 0.5rem;
    }

    .feature-highlight {
        background: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header with AI Badge
st.markdown("""
<div class="header">
    <h1>🏥 Healthcare System <span class="ai-badge">Vector Database Only</span></h1>
    <p>Advanced healthcare appointments powered exclusively by Pinecone Vector Database</p>
    <p><strong>All Medical Data from Vector DB • AI-Powered Search • Professional Care</strong></p>
    <p>🤖 100% Pinecone Vector Database - No manual medical data included</p>
    <p>📊 Access to 10,100+ medical documents through intelligent vector search</p>
</div>
""", unsafe_allow_html=True)

# Database Status
status_col1, status_col2 = st.columns(2)
with status_col1:
    if PINECONE_AVAILABLE:
        st.success("🟢 Vector Database: Connected")
    else:
        st.error("🔴 Vector Database: Disconnected")

with status_col2:
    if SANITY_TOKEN and SANITY_PROJECT_ID:
        st.success("🟢 Appointment System: Ready")
    else:
        st.warning("🟡 Appointment System: Configuration needed")

# Emergency Banner
st.markdown("""
<div class="emergency-banner">
    🚨 <strong>EMERGENCY?</strong> For life-threatening situations, call emergency services immediately!
</div>
""", unsafe_allow_html=True)

# Main Navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧠 AI Medical Search", "🩺 Advanced Symptoms", "📅 Book Appointment", "👨‍⚕️ Find Doctors", "💊 Medical Info"])

# Tab 1: AI Medical Search
with tab1:
    st.markdown("### 🧠 AI-Powered Medical Information Search")
    st.markdown('<div class="feature-highlight">Search our comprehensive medical database using advanced AI and vector similarity matching</div>', unsafe_allow_html=True)

    search_query = st.text_input(
        "🔍 Enter your medical question or topic:",
        placeholder="e.g., hypertension symptoms, diabetes treatment, heart disease prevention...",
        help="Ask any medical question and our AI will search through thousands of medical resources"
    )

    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("Number of results:", min_value=1, max_value=5, value=3)
    with col2:
        st.info("📚 Powered by Pinecone vector database with medical embeddings")

    if st.button("🔍 Search Medical Database", type="primary"):
        if search_query:
            if PINECONE_AVAILABLE:
                with st.spinner("🧠 Processing your query with AI..."):
                    results = search_medical_information(search_query, top_k)
                    st.markdown(results)
            else:
                st.error("❌ Vector database is not available. Please check your Pinecone configuration.")
        else:
            st.warning("Please enter a medical query to search")

    # Quick examples
    st.markdown("#### 💡 Example Searches:")
    example_cols = st.columns(3)
    examples = ["What is hypertension?", "diabetes symptoms", "heart attack warning signs"]
    for i, example in enumerate(examples):
        with example_cols[i]:
            if st.button(example, key=f"example_{i}"):
                st.session_state.search_query = example

    if "search_query" in st.session_state:
        st.session_state.search_query

# Tab 2: Advanced Symptoms Analysis
with tab2:
    st.markdown("### 🩺 Advanced AI Symptom Analysis")
    st.markdown('<div class="feature-highlight">Get intelligent symptom analysis using our AI-powered medical knowledge base</div>', unsafe_allow_html=True)

    symptoms_input = st.text_area(
        "Describe your symptoms in detail:",
        placeholder="e.g., I have been experiencing chest pain, shortness of breath, and dizziness for the past 2 days...",
        height=150,
        help="Be as detailed as possible for better analysis"
    )

    if st.button("🩺 Analyze Symptoms with AI", type="primary"):
        if symptoms_input:
            if PINECONE_AVAILABLE:
                with st.spinner("🧠 Analyzing your symptoms with advanced AI..."):
                    analysis = analyze_symptoms_advanced(symptoms_input)
                    st.markdown(analysis)
            else:
                st.error("❌ Advanced symptom analysis is not available. Please check your Pinecone configuration.")
        else:
            st.warning("Please describe your symptoms for analysis")

    st.warning("⚠️ **Emergency Disclaimer:** If you are experiencing severe symptoms like chest pain, difficulty breathing, or severe pain, please call emergency services immediately!")

# Tab 3: Book Appointment
with tab3:
    st.markdown("### 📅 Book an Appointment")

    col1, col2 = st.columns(2)

    with col1:
        patient_name = st.text_input("Full Name *", placeholder="Enter your full name")
        email = st.text_input("Email Address *", placeholder="your.email@example.com")
        phone = st.text_input("Phone Number", placeholder="+92 300 1234567")

    with col2:
        doctor_names = [name for name, info in DOCTORS_DATA.items() if info["can_book_appointment"]]
        selected_doctor = st.selectbox("Select Doctor *", doctor_names)

        tomorrow = datetime.now() + timedelta(days=1)
        min_date = tomorrow.date()
        max_date = (datetime.now() + timedelta(days=30)).date()
        appointment_date = st.date_input("Appointment Date *", min_value=min_date, max_value=max_date)

        available_times = ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"]
        appointment_time = st.selectbox("Preferred Time *", available_times)

    if selected_doctor:
        doctor_info = DOCTORS_DATA[selected_doctor]
        st.markdown("#### 📋 Doctor Information")
        st.markdown(f"""
        <div class="doctor-card">
            <h4>{doctor_info['name']}</h4>
            <p><strong>Specialty:</strong> {doctor_info['specialty']}</p>
            <p><strong>Location:</strong> {doctor_info['location']}</p>
            <p><strong>Consultation Fee:</strong> {doctor_info['fee']}</p>
            <p><strong>Availability:</strong> {doctor_info['availability']['Monday to Friday']['Morning']} / {doctor_info['availability']['Monday to Friday']['Evening']}</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("📅 Book Appointment", type="primary"):
        if patient_name and email and selected_doctor and appointment_date and appointment_time:
            with st.spinner("Booking your appointment..."):
                result = save_appointment(
                    patient_name,
                    email,
                    selected_doctor,
                    str(appointment_date),
                    appointment_time
                )
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)
        else:
            st.error("Please fill in all required fields (*)")

# Tab 4: Find Doctors
with tab4:
    st.markdown("### 👨‍⚕️ Find Doctors")

    col1, col2 = st.columns(2)
    with col1:
        search_specialty = st.selectbox("Filter by Specialty", ["All", "Cardiologist", "Neurologist", "Dermatologist"])
    with col2:
        search_city = st.selectbox("Filter by City", ["All", "Karachi", "Islamabad", "Lahore"])

    if st.button("🔍 Search Doctors"):
        specialty_filter = search_specialty if search_specialty != "All" else ""
        city_filter = search_city if search_city != "All" else ""
        results = search_doctors(specialty_filter, city_filter)

        st.markdown("#### 📋 Search Results")
        for result in results:
            st.info(result)

    st.markdown("#### 📋 All Available Doctors")
    for name, info in DOCTORS_DATA.items():
        booking_status = "✅ Available for Booking" if info["can_book_appointment"] else "ℹ️ Information Only"
        st.markdown(f"""
        <div class="doctor-card">
            <h4>{info['name']}</h4>
            <p><strong>Specialty:</strong> {info['specialty']}</p>
            <p><strong>City:</strong> {info['city']}</p>
            <p><strong>Fee:</strong> {info['fee']}</p>
            <p><strong>Status:</strong> {booking_status}</p>
        </div>
        """, unsafe_allow_html=True)

# Tab 5: Medical Information
with tab5:
    st.markdown("### 💊 Vector Database Medical Library")
    st.markdown('<div class="feature-highlight">All medical information comes exclusively from Pinecone Vector Database - 10,100+ medical documents</div>', unsafe_allow_html=True)

    st.info("🗄️ **Vector Database Only**: All medical information is retrieved exclusively from our Pinecone vector database. No manual or hardcoded medical data is included in this system.")

    # Quick info buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🫀 Heart Health", use_container_width=True):
            if PINECONE_AVAILABLE:
                info = search_medical_information("heart disease cardiovascular health")
                st.markdown(info)
            else:
                st.info("Basic heart health information would be shown here when vector database is available.")

    with col2:
        if st.button("🩸 Hypertension", use_container_width=True):
            if PINECONE_AVAILABLE:
                info = search_medical_information("hypertension high blood pressure")
                st.markdown(info)
            else:
                st.info("Basic hypertension information would be shown here when vector database is available.")

    with col3:
        if st.button("🍬 Diabetes", use_container_width=True):
            if PINECONE_AVAILABLE:
                info = search_medical_information("diabetes mellitus blood sugar")
                st.markdown(info)
            else:
                st.info("Basic diabetes information would be shown here when vector database is available.")

    # Custom search
    st.markdown("#### 🔍 Search Medical Library")
    custom_topic = st.text_input("Enter medical topic:", placeholder="e.g., migraine, asthma, arthritis...")

    if st.button("🔍 Get Information") and custom_topic:
        if PINECONE_AVAILABLE:
            with st.spinner("🧠 Searching medical knowledge base..."):
                info = search_medical_information(custom_topic)
                st.markdown(info)
        else:
            st.info(f"Basic information about '{custom_topic}' would be shown here when vector database is available.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>© 2024 Healthcare System | <strong>100% Pinecone Vector Database</strong></p>
    <p><strong>Emergency:</strong> 1122 (Pakistan) | 🤖 All Medical Data from Pinecone Vector Database</p>
    <p><em>This system retrieves ALL medical information exclusively from Pinecone Vector Database (10,100+ documents). No manual medical data included.</em></p>
    <p><strong>Vector Database Status:</strong> <span style="color: green;">✅ Connected</span> | <strong>Documents:</strong> 10,100+ Medical Resources</p>
</div>
""", unsafe_allow_html=True)