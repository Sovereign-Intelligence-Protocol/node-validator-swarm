import os, asyncio, base58, httpx, logging
from flask import Flask
from threading import Thread

# 1. ALIGNING ENVIRONMENTALS - DIRECT MAPPING
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID")) if os.getenv("TELEGRAM_ADMIN_ID") else 0
VAULT = os.getenv("VAULT_ADDRESS")
KEY = os.getenv("PRIVATE_KEY")
PORT = int(os.getenv("PORT", 10000))

# 2. RENDER HEARTBEAT (Binds to Port 10000)
app = Flask(__name__)
@app.route('/')
def health(): return "Sovereign Intelligence Protocol: Predator Live"

def run_heartbeat():
    app.run(host='0.0.0.0', port=PORT)

# 3. CORE SNIPER & TELEGRAM LOGIC
async def predator_scanner():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Surgical Execution Logic (Jito + Jupiter v6)
                logging.info(f"Scanning via Vault: {VAULT}")
                # [Sniper Logic Executes Here]
                await asyncio.sleep(120) # The 120s Delay you requested
            except Exception as e:
                logging.error(f"Scan Error: {e}")
                await asyncio.sleep(10)

async def handle_telegram():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    offset = 0
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params={"offset": offset, "timeout": 20})
                data = resp.json()
                for res in data.get("result", []):
                    offset = res["update_id"] + 1
                    msg = res.get("message", {})
                    if msg.get("from", {}).get("id") == ADMIN_ID:
                        # Bot only responds to YOUR ID
                        text = msg.get("text")
                        if text == "/start":
                            await client.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                             params={"chat_id": ADMIN_ID, "text": "Predator Online. Vault Active."})
        except Exception: pass
        await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Thread(target=run_heartbeat, daemon=True).start() # Starts Heartbeat on Port 10000
    loop = asyncio.get_event_loop()
    loop.create_task(handle_telegram())
    loop.run_until_complete(predator_scanner())
