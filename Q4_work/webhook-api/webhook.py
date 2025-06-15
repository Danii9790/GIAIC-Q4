from fastapi import FastAPI, Request
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Twilio setup
client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TWILIO_FROM = "whatsapp:+14155238886"  # Twilio Sandbox Number
PATIENT_NUMBER = "whatsapp:+923196560895"  # registered patient number

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
