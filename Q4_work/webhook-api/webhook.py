from fastapi import FastAPI, Request
from pydantic import BaseModel
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Twilio setup
client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TWILIO_FROM = "whatsapp:+14155238886"  # Twilio Sandbox Number
DOCTOR_NUMBER = "whatsapp:+923173762160"
PATIENT_NUMBER = "whatsapp:+923196560895"

@app.get("/")
async def root():
    return {"message": "Webhook is live from Vercel 🎉"}

class Appointment(BaseModel):
    patient_name: str
    doctor_name: str
    date: str
    time: str

@app.post("/set-appointment")
async def set_appointment(appointment: Appointment):
    print("📨 New Appointment Request:", appointment)
    try:
        msg = (
            f"📢 New Appointment:\n"
            f"👤 Patient: {appointment.patient_name}\n"
            f"🧑‍⚕️ Doctor: {appointment.doctor_name}\n"
            f"📅 Date: {appointment.date} at {appointment.time}\n\n"
            f"👉 Reply 'confirm' to approve."
        )
        client.messages.create(from_=TWILIO_FROM, to=DOCTOR_NUMBER, body=msg)
        return {"status": "success", "message": "Sent to doctor on WhatsApp."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.post("/whatsapp")
async def receive_whatsapp(request: Request):
    form = await request.form()

    # Debug: print all form fields
    print("📥 Form fields:", dict(form))

    message = form.get("Body", "").strip().lower()
    sender = form.get("From", "")

    print(f"📥 WhatsApp from {sender}: {message}")

    if message == "confirm" and sender == DOCTOR_NUMBER:
        client.messages.create(
            from_=TWILIO_FROM,
            to=PATIENT_NUMBER,
            body="✅ Doctor confirmed your appointment!"
        )
        print("✅ Confirmation sent to patient")
        return {"status": "sent"}

    print("❌ Ignored message or wrong sender")
    return {"status": "ignored"}
