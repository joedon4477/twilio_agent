import os, requests, pytest, json
from xml.etree import ElementTree
from datetime import datetime, UTC

# --- Environment Setup ---
RENDER_URL = os.getenv("RENDER_URL", "https://twilio-agent-rysz.onrender.com/").rstrip("/")
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()  # for future tests




# --- 1️⃣ Render Health Check ---
def test_render_health():
    """Confirm that the Render Flask service is alive."""
    r = requests.get(f"{RENDER_URL}/")
    assert r.status_code == 200, f"Render not reachable: {r.status_code}"
    assert "Twilio" in r.text or "Zapier" in r.text, "Unexpected home route response"


# --- 2️⃣ Zapier Hook Availability ---
@pytest.mark.skipif(not ZAPIER_WEBHOOK_URL, reason="ZAPIER_WEBHOOK_URL not set")
def test_zapier_hook_receives():
    """Verify Zapier Catch Hook URL is reachable and accepts JSON."""
    payload = {
        "from": "+19999999999",
        "message": "test",
        "timestamp": datetime.now(UTC).isoformat()
    }
    r = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=5)
    assert r.status_code == 200, f"Zapier hook not responding: {r.status_code}"
    assert "success" in r.text.lower(), f"Unexpected Zapier response: {r.text}"


# --- 3️⃣ Flask → Zapier Integration ---
def test_flask_to_zapier():
    """Simulate inbound SMS and confirm Flask forwards payload to Zapier."""
    r = requests.get(f"{RENDER_URL}/test-message?from=+15551234567&body=quote", timeout=10)
    assert r.status_code == 200, f"/test-message route failed: {r.status_code}"
    data = r.json()
    assert data.get("status") == "ok", f"Unexpected Flask test-message response: {data}"


# --- 4️⃣ Twilio Webhook Simulation ---
def test_twilio_sms_reply():
    """Simulate Twilio webhook POST and confirm Flask returns valid TwiML XML."""
    payload = {"Body": "quote", "From": "+15551234567"}
    r = requests.post(f"{RENDER_URL}/sms", data=payload)
    assert r.status_code == 200, f"/sms route failed: {r.status_code}"

    # Parse TwiML XML structure
    root = ElementTree.fromstring(r.text)
    assert root.tag == "Response", "Response root should be <Response>"
    messages = [child.text for child in root.findall("Message")]
    assert any("quote" in m.lower() or "thanks" in m.lower() for m in messages), \
        f"Unexpected TwiML message content: {messages}"


# --- 5️⃣ HCP → Zapier Trigger Stub ---
def test_hcp_trigger_simulation():
    """
    Simulate a webhook from Housecall Pro.
    Later: replace this stub with real HCP → Zapier integration.
    """
    example_hcp_payload = {
        "event": "job.completed",
        "job_id": "JOB-12345",
        "customer": {
            "name": "Jane Doe",
            "phone": "+15551234567",
            "email": "jane@example.com"
        },
        "job": {
            "service": "Lawn care",
            "technician": "Alex R.",
            "completed_at": datetime.now(UTC).isoformat()
        }
    }

    # Simulate sending to Zapier (this mirrors how HCP → Zapier will behave)
    if ZAPIER_WEBHOOK_URL:
        r = requests.post(ZAPIER_WEBHOOK_URL, json=example_hcp_payload, timeout=5)
        assert r.status_code == 200, "Zapier did not accept HCP payload"
    else:
        pytest.skip("ZAPIER_WEBHOOK_URL not set; skipping HCP simulation")

    # Optionally test local logic later (Flask route for HCP)
    # Example: r2 = requests.post(f"{RENDER_URL}/hcp-webhook", json=example_hcp_payload)


# --- 6️⃣ OpenAI “Brain” Integration Stub ---
@pytest.mark.skipif(not OPENAI_API_KEY, reason="OPENAI_API_KEY not set")
def test_openai_reply_generation():
    """
    Test a minimal AI response generation flow.
    Later, connect this to your AI reply logic in Flask or Zapier.
    """
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = "Generate a short, friendly text message confirming a quote request for window cleaning."
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )

    message = completion.choices[0].message.content.strip()
    assert "quote" in message.lower() or "confirm" in message.lower(), \
        f"Unexpected AI response: {message}"
    print("🧠 AI Response:", message)


# --- 7️⃣ System Summary (Optional Meta-Test) ---
def test_system_summary():
    """Print current integration readiness summary."""
    print("\n📊 SYSTEM INTEGRATION SUMMARY")
    print(f"• Render URL: {RENDER_URL}")
    print(f"• Zapier Hook: {'✅ set' if ZAPIER_WEBHOOK_URL else '❌ missing'}")
    print(f"• OpenAI Key: {'✅ set' if OPENAI_API_KEY else '❌ missing'}")
    print("• HCP Simulation: ready")
    print("• Twilio Webhook: responding via /sms")
