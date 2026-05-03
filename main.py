import os, asyncio, httpx
from flask import Flask

# --- 1. SECURE CONFIG ---
# These MUST be in your Render Environment tab
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

async def force_telegram_ping():
    if not TOKEN or not CHAT_ID:
        print("!!! CRITICAL: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in Render !!!")
        return

    async with httpx.AsyncClient() as client:
        # Clear old conflicts
        await client.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True")
        
        # Send fresh message
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": str(CHAT_ID).strip(), "text": "🎯 OMNICORE LIVE: Connection Reset Successfully.", "parse_mode": "Markdown"}
        
        r = await client.post(url, json=payload, timeout=15.0)
        print(f"TELEGRAM STATUS: {r.status_code}")
        print(f"TELEGRAM RESPONSE: {r.text}")

@app.route('/')
def home():
    try:
        # Force the message to send immediately
        asyncio.run(force_telegram_ping())
        return "OMNICORE: ONLINE", 200
    except Exception as e:
        print(f"PYTHON ERROR: {str(e)}")
        return f"ERROR: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
