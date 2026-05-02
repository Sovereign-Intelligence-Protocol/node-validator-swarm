import os
import asyncio
import threading
import base58
import httpx
from flask import Flask

# --- 1. THE HEARTBEAT (STOPS THE RENDER REBOOT) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Omnicore Monitor: Online", 200

def run_heartbeat():
    # Bind to Render's port immediately to prevent "No open ports" error
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_heartbeat, daemon=True).start()

# --- 2. TELEGRAM CONFIG ---
# Variables are pulled from Render Environment settings
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_tg(text):
    """Sends a message directly to your phone."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            print(f"Telegram Error: {e}")

# --- 3. MAIN MONITORING LOOP ---
async def monitor_loop():
    # This pings you the second the bot is actually stable
    await send_tg("🚀 S.I.P. Omnicore: Predator Engaged. System is stable.")
    
    while True:
        try:
            # Add your balance checking logic here
            print("Heartbeat: Bot is active and quiet.")
            await asyncio.sleep(3600) # One ping per hour
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
