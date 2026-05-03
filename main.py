import os, asyncio, httpx, base58
from flask import Flask

# --- LOAD SECRETS ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# Fallback to local string if env is missing (for testing ONLY)
# TOKEN = "YOUR_TOKEN_HERE" 
# CHAT_ID = "YOUR_CHAT_ID_HERE"

app = Flask(__name__)

async def force_send_ping():
    """Forces Telegram to talk, no matter what happened before."""
    if not TOKEN or not CHAT_ID:
        print("CRITICAL: Missing TOKEN or CHAT_ID in Render Environment!")
        return
        
    async with httpx.AsyncClient() as client:
        # 1. DELETE any old connection settings
        await client.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True")
        
        # 2. SEND the message
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": str(CHAT_ID).strip(), 
            "text": "🎯 OMNICORE ONLINE: Connection Hard-Reset Successful.",
            "parse_mode": "Markdown"
        }
        
        response = await client.post(url, json=payload, timeout=15.0)
        
        # 3. PRINT everything to logs
        print(f"DEBUG: Status Code: {response.status_code}")
        print(f"DEBUG: Telegram Response: {response.text}")

@app.route('/')
def home():
    # This triggers the message whenever Render pings the health check
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(force_send_ping())
        loop.close()
    except Exception as e:
        print(f"ERROR during trigger: {e}")
    return "SIP OMNICORE IS LIVE", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
