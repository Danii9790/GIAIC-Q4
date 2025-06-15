# from fastapi import FastAPI, Request
# from pydantic import BaseModel
# from twilio.rest import Client
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI()

# # Twilio setup
# client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
# TWILIO_FROM = "whatsapp:+14155238886"  # Twilio Sandbox Number
# DOCTOR_NUMBER = "whatsapp:+923173762160"
# PATIENT_NUMBER = "whatsapp:+923196560895"  # registered patient number


# # Root for testing
# @app.get("/")
# async def root():
#     return {"message": "Webhook is live!"}


# # -------------------- NEW ENDPOINT --------------------
# class Appointment(BaseModel):
#     patient_name: str
#     doctor_name: str
#     date: str
#     time: str


# @app.post("/set-appointment")
# async def set_appointment(appointment: Appointment):
#     try:
#         msg = (
#             f"📢 New Appointment Request:\n"
#             f"👤 Patient: {appointment.patient_name}\n"
#             f"🧑‍⚕️ Doctor: {appointment.doctor_name}\n"
#             f"📅 Date: {appointment.date} at {appointment.time}\n\n"
#             f"👉 *Reply with 'confirm'* to approve the appointment."
#         )

#         # Send WhatsApp to doctor
#         client.messages.create(
#             from_=TWILIO_FROM,
#             to=DOCTOR_NUMBER,
#             body=msg
#         )
#         return {"status": "success", "message": "Appointment request sent to doctor."}

#     except Exception as e:
#         return {"status": "error", "message": str(e)}


# # -------------------- EXISTING ENDPOINT --------------------
# @app.post("/whatsapp")
# async def receive_whatsapp(request: Request):
#     form = await request.form()
#     incoming_msg = form.get("Body", "").strip().lower()

#     if incoming_msg == "confirm":
#         client.messages.create(
#             from_=TWILIO_FROM,
#             to=PATIENT_NUMBER,
#             body="✅ Doctor confirmed your appointment!"
#         )
#         return {"status": "sent to patient"}

#     return {"status": "ignored"}

from fastapi import FastAPI, Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio Setup
TWILIO_FROM = "whatsapp:+14155238886"
DOCTOR_WHATSAPP = "whatsapp:+923173762160"
twilio_client = Client(os.getenv("TWILIO_ACC_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
PENDING_FILE = "/tmp/pending_appointments.json"  # Use /tmp for Vercel/Railway

app = FastAPI()

# Function to notify patient
def confirm_and_notify_patient(patient_name: str, doctor_name: str, date: str, time: str, patient_whatsapp: str) -> str:
    message = (
        f"✅ Hello {patient_name}, your appointment with {doctor_name} is confirmed for {date} at {time}."
    )
    try:
        twilio_client.messages.create(
            from_=TWILIO_FROM,
            to=patient_whatsapp,
            body=message
        )
        save_to_json(patient_name, doctor_name, date, time)
        return "✅ Confirmation sent to patient and saved."
    except Exception as e:
        return f"❌ Error notifying patient: {str(e)}"

# Save to JSON (confirmed appointments)
def save_to_json(patient_name, doctor_name, date, time):
    file = "/tmp/appointments.json"
    record = {
        "patient": patient_name,
        "doctor": doctor_name,
        "date": date,
        "time": time
    }
    if os.path.exists(file):
        with open(file, "r") as f:
            existing = json.load(f)
    else:
        existing = []
    existing.append(record)
    with open(file, "w") as f:
        json.dump(existing, f, indent=2)

# Endpoint to receive appointment requests from Streamlit
@app.post("/set-appointment")
async def set_appointment(data: dict):
    try:
        appointment = {
            "patient_name": data["patient_name"],
            "doctor_name": data["doctor_name"],
            "date": data["date"],
            "time": data["time"],
            "patient_whatsapp": data["patient_whatsapp"]
        }
        # Send WhatsApp message to doctor
        message = (
            f"📢 New Appointment Request:\n"
            f"Patient: {appointment['patient_name']}\n"
            f"Doctor: {appointment['doctor_name']}\n"
            f"Date: {appointment['date']} at {appointment['time']}\n\n"
            f"👉 Reply with 'confirm' to approve."
        )
        twilio_client.messages.create(
            from_=TWILIO_FROM,
            to=DOCTOR_WHATSAPP,
            body=message
        )
        # Save pending appointment
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, "r") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(appointment)
        with open(PENDING_FILE, "w") as f:
            json.dump(existing, f, indent=2)
        return {"status": "success", "message": "Appointment request sent to doctor"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Webhook endpoint for Twilio
@app.post("/webhook")
async def webhook(request: Request):
    try:
        form_data = await request.form()
        message_body = form_data.get("Body", "").strip().lower()
        from_number = form_data.get("From", "")

        # Check if the message is from the doctor and contains "confirm"
        if from_number == DOCTOR_WHATSAPP and message_body == "confirm":
            # Load pending appointments
            if os.path.exists(PENDING_FILE):
                with open(PENDING_FILE, "r") as f:
                    pending_appointments = json.load(f)
            else:
                return MessagingResponse().message("No pending appointments found.")

            # Process the most recent pending appointment
            if pending_appointments:
                appointment = pending_appointments.pop()  # Get the latest appointment
                patient_name = appointment["patient_name"]
                doctor_name = appointment["doctor_name"]
                date = appointment["date"]
                time = appointment["time"]
                patient_whatsapp = appointment["patient_whatsapp"]

                # Notify patient
                result = confirm_and_notify_patient(patient_name, doctor_name, date, time, patient_whatsapp)

                # Update pending appointments file
                with open(PENDING_FILE, "w") as f:
                    json.dump(pending_appointments, f, indent=2)

                # Respond to doctor
                response = MessagingResponse()
                response.message(f"✅ Appointment for {patient_name} confirmed and patient notified.")
                return response
            else:
                return MessagingResponse().message("No pending appointments to confirm.")
        else:
            return MessagingResponse().message("Please reply with 'confirm' to approve the appointment.")
    except Exception as e:
        return MessagingResponse().message(f"Error processing webhook: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)