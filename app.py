from flask import Flask, request, jsonify, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import requests, os, sys, json
from datetime import datetime, UTC

app = Flask(__name__)

# --- Load environment variables ---
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "").strip()
TWILIO_SID = os.getenv("TWILIO_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "").strip()

# --- Logging helper for clean structured output ---
def log_event(event_type, **data):
    payload = {"time": datetime.now(UTC).isoformat(), "event": event_type, **data}
    print(json.dumps(payload), file=sys.stdout, flush=True)


# --- Health / Root route (Render & uptime monitoring) ---
@app.route("/", methods=["GET"])
def health_check():
    log_event("health_check", status="ok")
    return "✅ Twilio + Zapier Flask service live", 200


# --- Twilio inbound webhook ---
@app.route("/sms", methods=["POST"])
def sms_reply():
    """Handle inbound SMS from Twilio, reply, and forward to Zapier."""
    body = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")

    log_event("incoming_sms", from_number=from_number, body=body)

    # Forward to Zapier webhook (non-blocking)
    if ZAPIER_WEBHOOK_URL:
        try:
            payload = {
                "from": from_number,
                "message": body,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            r = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=5)
            log_event("zapier_forward", status_code=r.status_code)
        except Exception as e:
            log_event("zapier_error", error=str(e))

    # Twilio reply logic
    resp = MessagingResponse()
    msg_lower = body.lower()

    if "quote" in msg_lower:
        resp.message("💬 Thanks! Your quote request has been received.")
    elif "hours" in msg_lower or "after" in msg_lower:
        resp.message("🕓 We’re open 8 AM – 6 PM, Mon–Fri. Reply 'quote' for pricing.")
    elif "hello" in msg_lower or "hi" in msg_lower:
        resp.message("👋 Hi there! Text 'quote' for pricing or 'hours' for availability.")
    else:
        resp.message(f"You said: {body}")

    log_event("reply_prepared", response=str(resp))
    return Response(str(resp), mimetype="application/xml")


# --- Twilio status callback (delivery confirmations) ---
@app.route("/status", methods=["POST"])
def sms_status():
    message_sid = request.form.get("MessageSid")
    message_status = request.form.get("MessageStatus")
    log_event("delivery_update", sid=message_sid, status=message_status)
    return "OK", 200


# --- Programmatic outbound (optional future use) ---
def send_sms(to: str, text: str):
    """Send SMS proactively using Twilio REST API (optional helper)."""
    if not (TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_NUMBER):
        log_event("send_sms_failed", reason="Missing Twilio credentials")
        return None

    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=text,
            from_=TWILIO_NUMBER,
            to=to,
            status_callback=f"{request.host_url}status"
        )
        log_event("send_sms", sid=msg.sid, to=to, body=text)
        return msg.sid
    except Exception as e:
        log_event("send_sms_error", error=str(e))
        return None


# --- Test route (safe simulation for Render + Zapier) ---
@app.route("/test-message", methods=["GET"])
def test_message():
    from_number = request.args.get("from", "+10000000000")
    body = request.args.get("body", "test").strip()
    log_event("test_message", from_number=from_number, body=body)

    if ZAPIER_WEBHOOK_URL:
        try:
            payload = {
                "from": from_number,
                "message": body,
                "timestamp": datetime.now(UTC).isoformat(),
                "source": "manual-test"
            }
            r = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=5)
            log_event("zapier_forward_test", status_code=r.status_code)
        except Exception as e:
            log_event("zapier_test_error", error=str(e))

    return jsonify({
        "status": "ok",
        "message": f"Simulated inbound SMS '{body}' from {from_number} forwarded to Zapier."
    }), 200


# --- Diagnostics route (internal snapshot) ---
@app.route("/diag", methods=["GET"])
def diagnostics():
    status = {
        "render_ok": True,
        "zapier_url_set": bool(ZAPIER_WEBHOOK_URL),
        "twilio_configured": bool(TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_NUMBER),
        "time": datetime.now(UTC).isoformat()
    }
    log_event("diagnostics_check", **status)
    return jsonify(status), 200


# --- Entrypoint for local runs ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
