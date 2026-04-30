import os, time, asyncio, threading, sys, signal, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- LIVE PRODUCTION LABELS ---
RPC = os.getenv("RPC_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID") # <--- FIXED: Pulls your actual ID
KEY = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
TIP = os.getenv("JITO_TIP_AMOUNT", "0.001")
THRESHOLD = os.getenv("CONFIDENCE_THRESHOLD", "0.85")
KRAKEN = os.getenv("KRAKEN_DEPOSIT_ADDRESS")
PORT, ACTIVE = int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN and ADMIN_ID: # <--- FIXED: Validates both exist
        async with httpx.AsyncClient() as c:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": ADMIN_ID, "text": f"OMNICORE: {m}"}
            await c.post(url, json=payload)

def handoff(s, f):
    global ACTIVE
    log("!!! SIGTERM: 120S MANUAL LAPSE STARTING !!!")
    ACTIVE = False
    time.sleep(120)
    os._exit(0)

signal.signal(signal.SIGTERM, handoff)

async def core_engine():
    log(f"==> OMNICORE V35.7 LIVE | WALLET: {WALLET[:6]}")
    await notify(f"Engine Armed on Slot Scanning.") # <--- Test message on startup
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                res = await client.get_slot()
                slot = res.value
                log(f"SCANNING SLOT: {slot}")
                await asyncio.sleep(2) 
            except Exception as e:
                log(f"CORE ERROR: {e}")
                await asyncio.sleep(5)

app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V35.7_STABLE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core_engine()), daemon=True).start()
    log(f"==> SERVER STARTING ON PORT {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
