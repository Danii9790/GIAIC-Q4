from fastapi import FastAPI, Request
from pydantic import BaseModel
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TWILIO_FROM = os.getenv("TWILIO_FROM") or "whatsapp:+14155238886"
DOCTOR_NUMBER = os.getenv("DOCTOR_NUMBER") or "whatsapp:+923173762160"
PATIENT_NUMBER = os.getenv("PATIENT_NUMBER") or "whatsapp:+923196560895"

@app.get("/")
async def root():
    return {"message": "Webhook is live!"}

class Appointment(BaseModel):
    patient_name: str
    doctor_name: str
    date: str
    time: str

@app.post("/set-appointment")
async def set_appointment(a: Appointment):
    print("📨 Received appointment:", a)
    msg = (
        f"📢 New Appointment Request:\n"
        f"👤 Patient: {a.patient_name}\n"
        f"🧑‍⚕️ Doctor: {a.doctor_name}\n"
        f"📅 Date: {a.date} at {a.time}\n\n"
        f"👉 Reply with 'confirm' to approve."
    )
    client.messages.create(from_=TWILIO_FROM, to=DOCTOR_NUMBER, body=msg)
    print("✅ WhatsApp sent to doctor")
    return {"status": "success", "message": "Appointment sent to doctor."}

@app.post("/whatsapp")
async def receive_whatsapp(request: Request):
    form = await request.form()
    incoming = form.get("Body", "").strip().lower()
    sender = form.get("From")
    print(f"📩 Incoming: {incoming} from {sender}")

    if incoming == "confirm" and sender == DOCTOR_NUMBER:
        client.messages.create(from_=TWILIO_FROM, to=PATIENT_NUMBER,
                               body="✅ Doctor confirmed your appointment!")
        print("✅ Confirmation sent to patient")
        return {"status": "sent to patient"}

    print("🚫 Ignored message")
    return {"status": "ignored"}
