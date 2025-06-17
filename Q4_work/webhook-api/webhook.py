import json
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
    try:
        form = await request.form()
        message = form.get("Body", "").strip().lower()
        sender = form.get("From", "")

        print(f"📥 WhatsApp from {sender}: {message}")

        if message == "confirm" and sender == DOCTOR_NUMBER:
            # ✅ Use WhatsApp Template Message
            client.messages.create(
                from_="whatsapp:+14155238886",  # Twilio Sandbox
                to=PATIENT_NUMBER,
                content_sid="HX860bd85736336b3bcffc4dfb3c3ac7df",
                content_variables=json.dumps({
                    "1": "Daniyal",         # 👤 Patient name
                    "2": "Dr. Ahmed",       # 🧑‍⚕️ Doctor name
                    "3": "Wednesday",       # 📅 Date
                    "4": "7PM"              # ⏰ Time
                })
            )
            print("✅ WhatsApp template sent to patient successfully")
            return {"status": "sent"}

        print("❌ Message ignored or sender mismatch")
        return {"status": "ignored"}

    except Exception as e:
        print("❌ Error in /whatsapp route:", str(e))
        return {"status": "error", "message": str(e)}
