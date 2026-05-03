import os, asyncio, httpx
from flask import Flask

# 1. IMMEDIATE CONFIG CHECK
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

async def send_emergency_ping():
    # If variables are missing, this will show up in your Render logs
    if not TOKEN: 
        print("CRITICAL ERROR: TELEGRAM_BOT_TOKEN is missing from Render Env!")
        return
    if not CHAT_ID:
        print("CRITICAL ERROR: TELEGRAM_CHAT_ID is missing from Render Env!")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": str(CHAT_ID).strip(), "text": "🎯 OMNICORE: Connection established.", "parse_mode": "Markdown"}
    
    async with httpx.AsyncClient() as client:
        # Force clear any old webhooks
        await client.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True")
        r = await client.post(url, json=payload, timeout=15.0)
        print(f"TELEGRAM STATUS: {r.status_code}")
        print(f"TELEGRAM RESPONSE: {r.text}")

@app.route('/')
def home():
    try:
        asyncio.run(send_emergency_ping())
        return "SUCCESS", 200
    except Exception as e:
        print(f"PYTHON ERROR: {e}")
        return f"FAILED: {e}", 500

if __name__ == "__main__":
    # Render requires port 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
