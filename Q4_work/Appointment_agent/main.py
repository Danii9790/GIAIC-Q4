import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# --------------GMAIL CONFIGURATION--------------
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ----------------- TWILIO CONFIG -------------------
TWILIO_SID = os.getenv("TWILIO_ACC_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = "whatsapp:+14155238886"
TWILIO_TEMPLATE_ID = "HXb5b62575e6e4ff6129ad7c8efe1f983e"
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

# ----------------- GEMINI SETUP -------------------
gemini_api_key = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# Doctor's verified WhatsApp numbers (for trial)
DOCTOR_CONTACTS = {
    "Dr. Khan": "whatsapp:+923173762160"
}

import smtplib
from email.message import EmailMessage

# Email Function
def send_email_to_patient(to_email, patient_name, doctor_name, date, time):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Appointment Confirmation with {doctor_name}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg.set_content(
            f"Dear {patient_name},\n\nYour appointment with {doctor_name} is confirmed for {date} at {time}.\n\nThank you!"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        print("Failed to send email:", e)

# ----------------- FUNCTION TOOLS -------------------
@function_tool
def get_doctors() -> dict:
    return {
        "Dr. Smith": {
            "specialty": "Cardiologist",
            "availability": {
                "Monday": "10AM - 2PM",
                "Wednesday": "11AM - 3PM",
                "Friday": "9AM - 1PM"
            }
        },
        "Dr. Khan": {
            "specialty": "Dermatologist",
            "availability": {
                "Tuesday": "12PM - 4PM",
                "Thursday": "10AM - 1PM"
            }
        },
        "Dr. Patel": {
            "specialty": "Pediatrician",
            "availability": {
                "Monday": "9AM - 12PM",
                "Wednesday": "2PM - 5PM"
            }
        },
        "Dr. Lee": {
            "specialty": "Orthopedic",
            "availability": {
                "Tuesday": "11AM - 2PM",
                "Thursday": "1PM - 4PM"
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
def send_whatsapp_confirmation(patient_name: str, doctor_name: str, date: str, time: str, patient_email: str) -> str:
    doctor_whatsapp = DOCTOR_CONTACTS.get(doctor_name)
    if not doctor_whatsapp:
        return "❌ Doctor contact not found or not verified for Twilio trial."

    try:
        # Step 1: Notify Doctor
        twilio_client.messages.create(
            from_=TWILIO_FROM,
            to=doctor_whatsapp,
            content_sid=TWILIO_TEMPLATE_ID,
            content_variables=f'{{"1":"{patient_name}", "2":"{date} at {time}"}}'
        )

        # Step 2: Simulate approval & email patient
        send_email_to_patient(patient_email, patient_name, doctor_name, date, time)
        return f"✅ Request sent to {doctor_name}. Confirmation email sent to {patient_email}."

    except Exception as e:
        return f"❌ Failed to send WhatsApp or email: {str(e)}"


# ----------------- AGENT -------------------
agent = Agent(
    name="Appointment Assistant",
    instructions="""
You are a helpful assistant for booking doctor appointments.

1. When a user asks about doctor availability or specialization, use the get_doctors function.
2. When a user wants to book an appointment, ask for their name, doctor, date, time, and email.
3. Use send_whatsapp_confirmation to notify the doctor and confirm via email to the patient.
4. Always speak politely and be helpful.
""",
    model=model,
    tools=[get_doctors, send_whatsapp_confirmation]
)


# Chainlit Handlers
@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="👋 Hello! I’m your Doctor Appointment Assistant. How may I help you today?").send()

@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    result = await cl.make_async(Runner.run_sync)(agent, input=history)
    response_text = result.final_output

    await cl.Message(content=response_text).send()
    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)



