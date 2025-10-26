from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Health check / root route (keeps Render happy) ---
@app.route("/", methods=["GET"])
def home():
    return "✅ Twilio Agent running", 200


# --- Main SMS route ---
@app.route("/sms", methods=["POST"])
def sms_reply():
    """Handle incoming SMS and send a basic reply."""

    body = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    print(f"📩 Incoming message from {from_number}: {body}")

    resp = MessagingResponse()

    # --- Basic demo logic ---
    lower = body.lower()
    if "quote" in lower:
        resp.message("💬 Thanks! Our standard service quote is $125/hr.")
    elif "hours" in lower or "after" in lower:
        resp.message("🕓 We’re open 8 AM – 6 PM, Mon–Fri. Reply 'quote' for pricing.")
    elif "hello" in lower or "hi" in lower:
        resp.message("👋 Hi there! Text 'quote' for pricing or 'hours' for availability.")
    else:
        resp.message(f"You said: {body}")

    print("✅ Reply prepared and sent via Twilio.")
    return str(resp)


# --- For local debugging only ---
if __name__ == "__main__":
    # Render will override PORT with an env variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
