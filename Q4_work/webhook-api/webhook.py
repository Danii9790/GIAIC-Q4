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
PATIENT_NUMBER = "whatsapp:+923196560895"  # registered patient number


# Root for testing
@app.get("/")
async def root():
    return {"message": "Webhook is live!"}


# -------------------- NEW ENDPOINT --------------------
class Appointment(BaseModel):
    patient_name: str
    doctor_name: str
    date: str
    time: str


@app.post("/set-appointment")
async def set_appointment(appointment: Appointment):
    try:
        msg = (
            f"📢 New Appointment Request:\n"
            f"👤 Patient: {appointment.patient_name}\n"
            f"🧑‍⚕️ Doctor: {appointment.doctor_name}\n"
            f"📅 Date: {appointment.date} at {appointment.time}\n\n"
            f"👉 *Reply with 'confirm'* to approve the appointment."
        )

        # Send WhatsApp to doctor
        client.messages.create(
            from_=TWILIO_FROM,
            to=DOCTOR_NUMBER,
            body=msg
        )
        return {"status": "success", "message": "Appointment request sent to doctor."}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- EXISTING ENDPOINT --------------------
@app.post("/whatsapp")
async def receive_whatsapp(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body", "").strip().lower()

    if incoming_msg == "confirm":
        client.messages.create(
            from_=TWILIO_FROM,
            to=PATIENT_NUMBER,
            body="✅ Doctor confirmed your appointment!"
        )
        return {"status": "sent to patient"}

    return {"status": "ignored"}
