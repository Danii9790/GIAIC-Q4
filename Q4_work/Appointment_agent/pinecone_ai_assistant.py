import streamlit as st
import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
from typing import Dict, List
import openai

# -------------------- Load Environment --------------------
load_dotenv()

# -------------------- Pinecone Setup --------------------
PINECONE_AVAILABLE = False
healthcare_index = None
embedding_client = None

def initialize_pinecone():
    """Initialize Pinecone connection"""
    global PINECONE_AVAILABLE, healthcare_index, embedding_client

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
        return True

    except Exception as e:
        st.error(f"⚠️ Pinecone connection failed: {e}")
        PINECONE_AVAILABLE = False
        return False

# -------------------- Simple Doctor Database --------------------
DOCTORS_DB = {
    "Dr. Ahmed Khan": {
        "name": "Dr. Ahmed Khan",
        "specialty": "Cardiologist",
        "expertise": ["Heart Disease", "Hypertension", "Chest Pain", "Arrhythmia", "Heart Failure"],
        "city": "Karachi",
        "location": "Karachi, Pakistan",
        "experience": "15+ years",
        "fee": "Rs 2000",
        "rating": 4.8,
        "availability": {
            "Monday to Friday": {
                "Morning": "10:00 AM - 2:00 PM",
                "Evening": "7:00 PM - 10:00 PM"
            }
        },
        "can_book_appointment": True,
        "contact": "+92 21 1234567"
    },
    "Dr. Khan": {
        "name": "Dr. Khan",
        "specialty": "Neurologist",
        "expertise": ["Headache", "Migraine", "Stroke", "Epilepsy", "Brain Disorders"],
        "city": "Islamabad",
        "location": "Islamabad, Pakistan",
        "experience": "12+ years",
        "fee": "Rs 2500",
        "rating": 4.7,
        "availability": {
            "Monday to Friday": {
                "Morning": "9:00 AM - 1:00 PM",
                "Evening": "6:00 PM - 9:00 PM"
            }
        },
        "can_book_appointment": True,
        "contact": "+92 51 2345678"
    },
    "Dr. Sarah Ali": {
        "name": "Dr. Sarah Ali",
        "specialty": "Dermatologist",
        "expertise": ["Skin Diseases", "Acne", "Eczema", "Psoriasis", "Allergies"],
        "city": "Lahore",
        "location": "Lahore, Pakistan",
        "experience": "10+ years",
        "fee": "Rs 1500",
        "rating": 4.6,
        "availability": {
            "Monday to Friday": {
                "Morning": "9:00 AM - 1:00 PM",
                "Evening": "6:00 PM - 9:00 PM"
            }
        },
        "can_book_appointment": False,
        "contact": "+92 42 3456789"
    },
    "Dr. Fatima Zafar": {
        "name": "Dr. Fatima Zafar",
        "specialty": "General Physician",
        "expertise": ["General Health", "Primary Care", "Preventive Medicine", "Common Illnesses"],
        "city": "Karachi",
        "location": "Karachi, Pakistan",
        "experience": "8+ years",
        "fee": "Rs 1200",
        "rating": 4.5,
        "availability": {
            "Monday to Saturday": {
                "Morning": "8:00 AM - 2:00 PM",
                "Evening": "5:00 PM - 9:00 PM"
            }
        },
        "can_book_appointment": True,
        "contact": "+92 21 9876543"
    },
    "Dr. Omar Hassan": {
        "name": "Dr. Omar Hassan",
        "specialty": "Orthopedic Surgeon",
        "expertise": ["Bone Fractures", "Joint Pain", "Arthritis", "Sports Injuries", "Back Pain"],
        "city": "Islamabad",
        "location": "Islamabad, Pakistan",
        "experience": "18+ years",
        "fee": "Rs 3000",
        "rating": 4.9,
        "availability": {
            "Monday to Friday": {
                "Morning": "10:00 AM - 2:00 PM",
                "Evening": "6:00 PM - 8:00 PM"
            }
        },
        "can_book_appointment": True,
        "contact": "+92 51 8765432"
    }
}

# -------------------- Pinecone Functions --------------------
def create_embedding(text: str) -> List[float]:
    """Create embedding for text"""
    if not embedding_client:
        raise Exception("Embedding client not available")

    try:
        response = embedding_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        return embedding[:768]  # Truncate to 768 dimensions
    except Exception as e:
        raise Exception(f"Failed to create embedding: {e}")

def search_medical_knowledge(query: str, top_k: int = 5) -> List[Dict]:
    """Search medical knowledge using Pinecone"""
    if not PINECONE_AVAILABLE:
        return []

    try:
        query_embedding = create_embedding(query)

        search_results = healthcare_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        results = []
        for match in search_results.get("matches", []):
            results.append({
                "source": match["metadata"].get("source_file", "Unknown"),
                "text": match["metadata"].get("text", ""),
                "score": match.get("score", 0),
                "disease": match["metadata"].get("disease", ""),
                "symptoms": match["metadata"].get("symptoms", "")
            })

        return results

    except Exception as e:
        st.error(f"Error searching medical knowledge: {e}")
        return []

def analyze_symptoms_with_ai(symptoms: str) -> Dict:
    """Analyze symptoms using Pinecone AI"""
    if not PINECONE_AVAILABLE:
        return {
            "analysis": "AI symptom analysis is currently unavailable. Please consult a healthcare professional directly.",
            "recommendations": ["Consult with Dr. Ahmed Khan (Cardiologist) or Dr. Khan (Neurologist) for evaluation."],
            "urgency": "medium"
        }

    # Check for emergency symptoms first
    emergency_keywords = ["chest pain", "difficulty breathing", "severe pain", "emergency", "unconscious", "stroke", "bleeding"]
    if any(keyword in symptoms.lower() for keyword in emergency_keywords):
        return {
            "analysis": "🚨 **EMERGENCY - IMMEDIATE MEDICAL ATTENTION REQUIRED**\n\nBased on your symptoms, you may be experiencing a medical emergency.",
            "recommendations": [
                "Call emergency services immediately (1122 in Pakistan)",
                "Go to the nearest emergency room",
                "Do not wait - seek immediate medical attention"
            ],
            "urgency": "emergency"
        }

    try:
        # Search for relevant medical information
        enhanced_query = f"symptoms diagnosis medical conditions treatment {symptoms} healthcare"
        search_results = search_medical_knowledge(enhanced_query, top_k=5)

        # Build analysis
        analysis = f"**Symptom Analysis**\n\n**Reported Symptoms:** {symptoms}\n\n"

        if search_results:
            analysis += f"**Found {len(search_results)} relevant medical records:**\n\n"

            # Add relevant conditions found
            conditions_found = set()
            for result in search_results:
                if result.get("disease"):
                    conditions_found.add(result["disease"])

            if conditions_found:
                analysis += f"**Possible Related Conditions:**\n"
                for condition in list(conditions_found)[:3]:
                    analysis += f"• {condition}\n"
                analysis += "\n"

        # Doctor recommendations based on symptoms
        recommendations = []
        symptoms_lower = symptoms.lower()

        if any(keyword in symptoms_lower for keyword in ["chest", "heart", "palpitation", "blood pressure", "shortness of breath"]):
            recommendations.append("🫀 **Dr. Ahmed Khan (Cardiologist)** - Heart conditions, chest pain, blood pressure issues")

        if any(keyword in symptoms_lower for keyword in ["headache", "migraine", "dizziness", "brain", "numbness", "tingling", "seizure"]):
            recommendations.append("🧠 **Dr. Khan (Neurologist)** - Headaches, neurological symptoms, brain conditions")

        if any(keyword in symptoms_lower for keyword in ["skin", "rash", "acne", "dermatology", "allergy", "itching"]):
            recommendations.append("🔬 **Dr. Sarah Ali (Dermatologist)** - Skin conditions, rashes, allergic reactions")

        if any(keyword in symptoms_lower for keyword in ["bone", "joint", "fracture", "arthritis", "back pain", "sports injury"]):
            recommendations.append("🦴 **Dr. Omar Hassan (Orthopedic Surgeon)** - Bone and joint conditions")

        if not recommendations:
            recommendations.append("🩺 **Dr. Fatima Zafar (General Physician)** - General health evaluation and primary care")

        # Next steps
        next_steps = [
            "Monitor your symptoms closely",
            "Keep a symptom diary",
            "Schedule an appointment with recommended specialist",
            "If symptoms worsen, seek immediate medical attention"
        ]

        urgency = "medium"
        if any(keyword in symptoms_lower for keyword in ["severe", "worst", "unbearable"]):
            urgency = "high"
        elif any(keyword in symptoms_lower for keyword in ["mild", "slight", "minor"]):
            urgency = "low"

        return {
            "analysis": analysis,
            "recommendations": recommendations,
            "next_steps": next_steps,
            "urgency": urgency,
            "search_results": search_results[:3]  # Top 3 results for display
        }

    except Exception as e:
        return {
            "analysis": f"Error analyzing symptoms: {str(e)}",
            "recommendations": ["Please consult a healthcare professional for proper evaluation."],
            "urgency": "medium"
        }

def find_doctors_for_symptoms(symptoms: str) -> List[Dict]:
    """Find appropriate doctors for specific symptoms"""
    symptoms_lower = symptoms.lower()
    recommended_doctors = []

    for name, info in DOCTORS_DB.items():
        relevance_score = 0

        # Check symptom relevance to doctor's expertise
        for expertise in info["expertise"]:
            expertise_lower = expertise.lower()

            # Direct symptom matching
            if any(keyword in symptoms_lower for keyword in expertise_lower.split()):
                relevance_score += 3

            # Related symptom matching
            if "heart" in symptoms_lower and "heart" in expertise_lower:
                relevance_score += 3
            elif "headache" in symptoms_lower and any(keyword in symptoms_lower for keyword in ["headache", "migraine", "brain"]):
                relevance_score += 3
            elif "pain" in symptoms_lower and "pain" in expertise_lower:
                relevance_score += 2
            elif "skin" in symptoms_lower and any(keyword in symptoms_lower for keyword in ["skin", "rash", "acne"]):
                relevance_score += 3
            elif "bone" in symptoms_lower or "joint" in symptoms_lower:
                relevance_score += 3

        if relevance_score > 0:
            doctor_info = info.copy()
            doctor_info["relevance_score"] = relevance_score
            recommended_doctors.append(doctor_info)

    # Sort by relevance score
    recommended_doctors.sort(key=lambda x: x["relevance_score"], reverse=True)

    return recommended_doctors

# -------------------- UI Functions --------------------
def display_doctor_card(doctor: Dict, show_relevance: bool = False):
    """Display doctor information in a card format"""
    relevance_badge = f" 🎯 Relevance: {doctor.get('relevance_score', 0)}" if show_relevance else ""

    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: #f9f9f9;
            border-left: 5px solid #4CAF50;
        ">
            <h4>👨‍⚕️ {doctor['name']}{relevance_badge}</h4>
            <p><strong>Specialty:</strong> {doctor['specialty']}</p>
            <p><strong>Expertise:</strong> {', '.join(doctor['expertise'][:3])}</p>
            <p><strong>Location:</strong> {doctor['location']}</p>
            <p><strong>Experience:</strong> {doctor['experience']}</p>
            <p><strong>Consultation Fee:</strong> {doctor['fee']}</p>
            <p><strong>Rating:</strong> ⭐ {doctor['rating']}</p>
            <p><strong>Contact:</strong> {doctor['contact']}</p>
            <p><strong>Availability:</strong> {doctor['availability']['Monday to Friday']['Morning']} / {doctor['availability']['Monday to Friday']['Evening']}</p>
        </div>
        """, unsafe_allow_html=True)

# -------------------- Main Streamlit App --------------------
def main():
    # Configure Streamlit page
    st.set_page_config(
        page_title="AI Healthcare Assistant",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            color: white;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: #e8f5e8;
            border-left: 4px solid #4CAF50;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
        }
        .emergency-banner {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: bold;
        }
        .doctor-badge {
            background: linear-gradient(45deg, #2196F3, #1976D2);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize Pinecone
    if not initialize_pinecone():
        st.error("🚨 **Critical Error**: Unable to connect to Pinecone database. Some features may not work properly.")

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 AI Healthcare Assistant</h1>
        <p>Pinecone-Powered Doctor Finder & Symptom Analysis</p>
        <p><strong>🤖 100% AI-Powered • 🧠 Smart Analysis • 👨‍⚕️ Expert Matching</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "🟢 Connected" if PINECONE_AVAILABLE else "🔴 Disconnected"
        st.metric("Pinecone AI", status)
    with col2:
        st.metric("Available Doctors", len(DOCTORS_DB))
    with col3:
        st.metric("Specialties", len(set(doc['specialty'] for doc in DOCTORS_DB.values())))

    # Emergency banner
    st.markdown("""
    <div class="emergency-banner">
        🚨 <strong>EMERGENCY?</strong> For life-threatening situations, call emergency services immediately (1122)!
    </div>
    """, unsafe_allow_html=True)

    # Main navigation
    tab1, tab2, tab3 = st.tabs(["🩺 AI Symptom Analysis", "👨‍⚕️ Find Doctor", "🏥 All Doctors"])

    # Tab 1: AI Symptom Analysis
    with tab1:
        st.markdown("### 🩺 AI-Powered Symptom Analysis")
        st.markdown('<div class="feature-card">Describe your symptoms and our AI will analyze them using Pinecone vector database technology</div>', unsafe_allow_html=True)

        symptoms_input = st.text_area(
            "Describe your symptoms in detail:",
            placeholder="e.g., I have been experiencing chest pain, shortness of breath, and dizziness for the past 2 days...",
            height=120,
            help="Be as detailed as possible for better AI analysis"
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            analyze_button = st.button("🧠 Analyze Symptoms with AI", type="primary", use_container_width=True)
        with col2:
            st.info("💡 Powered by\n10,100+ medical documents")

        if analyze_button and symptoms_input:
            with st.spinner("🧠 AI analyzing symptoms..."):
                analysis_result = analyze_symptoms_with_ai(symptoms_input)

                # Display urgency indicator
                urgency_colors = {
                    "emergency": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                urgency_text = analysis_result["urgency"].upper()
                st.markdown(f"### {urgency_colors.get(analysis_result['urgency'], '🟡')} **URGENCY LEVEL: {urgency_text}**")

                # Display analysis
                st.markdown("#### 📋 AI Analysis")
                st.markdown(analysis_result["analysis"])

                # Display medical knowledge results if available
                if analysis_result.get("search_results"):
                    st.markdown("#### 📚 Medical Knowledge Base Results")
                    for i, result in enumerate(analysis_result["search_results"], 1):
                        with st.expander(f"📄 Result {i}: {result['source']} (Relevance: {result['score']:.1%})"):
                            st.write(f"**Disease:** {result.get('disease', 'N/A')}")
                            st.write(f"**Symptoms:** {result.get('symptoms', 'N/A')}")
                            st.write(f"**Details:** {result['text'][:300]}...")

                # Display doctor recommendations
                st.markdown("#### 👨‍⚕️ Recommended Doctors")
                for rec in analysis_result["recommendations"]:
                    st.info(rec)

                # Display next steps
                st.markdown("#### 📋 Next Steps")
                for step in analysis_result.get("next_steps", []):
                    st.write(f"• {step}")

        st.warning("⚠️ **Medical Disclaimer**: This AI analysis is for informational purposes only and is not a substitute for professional medical diagnosis. Always consult qualified healthcare professionals.")

    # Tab 2: Find Doctor
    with tab2:
        st.markdown("### 👨‍⚕️ Smart Doctor Finder")
        st.markdown('<div class="feature-card">Find the right doctor based on your symptoms or medical needs using AI-powered matching</div>', unsafe_allow_html=True)

        # Search options
        search_method = st.radio("Search Method:", ["By Symptoms", "By Specialty", "By Location"])

        if search_method == "By Symptoms":
            st.markdown("#### 🔍 Find Doctor by Symptoms")
            symptom_search = st.text_input(
                "Enter your symptoms or medical condition:",
                placeholder="e.g., chest pain, headache, skin rash, joint pain...",
                help="Our AI will match you with the most appropriate specialists"
            )

            if st.button("🔍 Find Doctors for These Symptoms"):
                if symptom_search:
                    with st.spinner("🧠 AI finding best doctors for your symptoms..."):
                        recommended_doctors = find_doctors_for_symptoms(symptom_search)

                        if recommended_doctors:
                            st.success(f"Found {len(recommended_doctors)} doctors relevant to your symptoms")
                            for doctor in recommended_doctors:
                                display_doctor_card(doctor, show_relevance=True)
                        else:
                            st.warning("No specific matches found. Showing all general physicians...")
                            for name, info in DOCTORS_DB.items():
                                if info["specialty"] == "General Physician":
                                    display_doctor_card(info)

        elif search_method == "By Specialty":
            st.markdown("#### 🏥 Find Doctor by Specialty")

            specialties = list(set(doc['specialty'] for doc in DOCTORS_DB.values()))
            selected_specialty = st.selectbox("Select Specialty:", ["All"] + specialties)

            if selected_specialty != "All":
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 📋 Available Specialists")
                    for name, info in DOCTORS_DB.items():
                        if info["specialty"] == selected_specialty:
                            display_doctor_card(info)

        else:  # By Location
            st.markdown("#### 📍 Find Doctor by Location")

            cities = list(set(doc['city'] for doc in DOCTORS_DB.values()))
            selected_city = st.selectbox("Select City:", ["All"] + cities)

            if selected_city != "All":
                st.markdown(f"#### 📍 Doctors in {selected_city}")
                for name, info in DOCTORS_DB.items():
                    if info["city"] == selected_city:
                        display_doctor_card(info)

    # Tab 3: All Doctors
    with tab3:
        st.markdown("### 🏥 All Available Doctors")
        st.markdown('<div class="feature-card">Browse our complete directory of healthcare professionals</div>', unsafe_allow_html=True)

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_specialty = st.selectbox("Filter by Specialty:", ["All"] + list(set(doc['specialty'] for doc in DOCTORS_DB.values())))
        with col2:
            filter_city = st.selectbox("Filter by City:", ["All"] + list(set(doc['city'] for doc in DOCTORS_DB.values())))

        # Display doctors with filters
        doctors_to_show = []
        for name, info in DOCTORS_DB.items():
            if filter_specialty != "All" and info["specialty"] != filter_specialty:
                continue
            if filter_city != "All" and info["city"] != filter_city:
                continue
            doctors_to_show.append(info)

        if doctors_to_show:
            st.success(f"Found {len(doctors_to_show)} doctors matching your criteria")
            for doctor in doctors_to_show:
                display_doctor_card(doctor)
        else:
            st.info("No doctors found matching your criteria. Try adjusting filters.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>© 2024 AI Healthcare Assistant | 🤖 Powered by Pinecone Vector Database</p>
        <p><strong>Emergency:</strong> 1122 (Pakistan) | 📊 <span class="doctor-badge">10,100+ Medical Documents</span></p>
        <p><em>All medical analysis powered by AI vector search technology. Always consult healthcare professionals for medical advice.</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()