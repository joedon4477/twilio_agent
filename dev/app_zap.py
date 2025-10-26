from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests, os
from datetime import datetime

app = Flask(__name__)

ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "").strip()

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint for Render."""
    return "✅ Twilio + Zapier Flask demo running", 200


@app.route("/sms", methods=["POST"])
def sms_reply():
    """Handle incoming SMS and forward data to Zapier."""
    body = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    print(f"📩 Incoming message from {from_number}: {body}")

    # Forward to Zapier webhook
    if ZAPIER_WEBHOOK_URL:
        try:
            payload = {
                "from": from_number,
                "message": body,
                "timestamp": datetime.utcnow().isoformat()
            }
            r = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=5)
            print(f"📤 Sent to Zapier: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Zapier webhook failed: {e}")

    # Prepare Twilio XML reply (Twilio trial will block delivery, but this keeps logic working)
    resp = MessagingResponse()
    lower = body.lower()

    if "quote" in lower:
        resp.message("💬 Thanks! Your quote request has been received.")
    elif "hours" in lower:
        resp.message("🕓 We’re open 8 AM – 6 PM, Mon–Fri. Reply 'quote' for pricing.")
    else:
        resp.message("👋 Hi there! Text 'quote' for pricing or 'hours' for availability.")

    print("✅ Twilio webhook handled successfully.")
    return Response(str(resp), mimetype="application/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
