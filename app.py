
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

@app.route("/sms", methods=["POST"])
def sms_reply():
    msg = request.form.get("Body", "")
    resp = MessagingResponse()
    resp.message(f"You said: {msg}")
    return str(resp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
