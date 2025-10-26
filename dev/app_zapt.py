from flask import Flask, request, jsonify, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests, os
from datetime import datetime

app = Flask(__name__)

# --- Environment variables ---
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "").strip()

# --- Root route (Render health check) ---
@app.route("/", methods=["GET"])
def health_check():
    return "✅ Twilio + Zapier Flask demo running", 200


# --- Twilio webhook route ---
@app.route("/sms", methods=["POST"])
def sms_reply():
    """Handle incoming SMS from Twilio and forward to Zapier."""
    body = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    print(f"📩 Incoming message from {from_number}: {body}")

    # --- Forward to Zapier webhook ---
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

    # --- Generate Twilio-compatible response ---
    resp = MessagingResponse()
    lower = body.lower()

    if "quote" in lower:
        resp.message("💬 Thanks! Your quote request has been received.")
    elif "hours" in lower or "after" in lower:
        resp.message("🕓 We’re open 8 AM – 6 PM, Mon–Fri. Reply 'quote' for pricing.")
    else:
        resp.message("👋 Hi there! Text 'quote' for pricing or 'hours' for availability.")

    print("✅ Twilio webhook handled successfully.")
    return Response(str(resp), mimetype="application/xml")


# --- Test route for browser/local simulation ---
@app.route("/test-message", methods=["GET"])
def test_message():
    """
    Simulate an incoming SMS without Twilio.
    Example:
      https://your-app.onrender.com/test-message?from=+15551234567&body=quote
    """
    from_number = request.args.get("from", "+10000000000")
    body = request.args.get("body", "test").strip()
    print(f"🧪 Simulated test message from {from_number}: {body}")

    # Send to Zapier as if Twilio triggered it
    if ZAPIER_WEBHOOK_URL:
        try:
            payload = {
                "from": from_number,
                "message": body,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "manual-test"
            }
            r = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=5)
            print(f"📤 (Simulated) Sent to Zapier: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Zapier webhook failed during test: {e}")

    return jsonify({
        "status": "ok",
        "message": f"Simulated inbound SMS '{body}' from {from_number} forwarded to Zapier."
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
