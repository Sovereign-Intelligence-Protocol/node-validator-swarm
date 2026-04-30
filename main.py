import os, time, asyncio, threading, sys, signal, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- VERIFIED DASHBOARD LABELS ---
RPC = os.getenv("RPC_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
KEY = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
WALLET = os.getenv("SOLANA_WALLET_ADDRESS", "N/A")
TIP = os.getenv("JITO_TIP_AMOUNT", "0.001")
PORT, ACTIVE = int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if not TOKEN or not ADMIN_ID:
        log("TELEGRAM ERROR: Missing TOKEN or ADMIN_ID in dashboard")
        return
    try:
        async with httpx.AsyncClient() as c:
            res = await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                               json={"chat_id": ADMIN_ID, "text": f"OMNICORE: {m}"})
            if res.status_code != 200: log(f"TELEGRAM FAIL: {res.text}")
    except Exception as e: log(f"NOTIFY ERROR: {e}")

def handoff(s, f):
    global ACTIVE
    log("!!! SIGTERM: 120S MANUAL LAPSE STARTING !!!")
    ACTIVE = False
    time.sleep(120)
    os._exit(0)

signal.signal(signal.SIGTERM, handoff)

async def core_engine():
    log(f"==> OMNICORE V35.7 LIVE | WALLET: {WALLET[:6]}")
    await notify("Engine Armed. Scanning Mainnet Slots.")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                # Production Jup/Jito logic here
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
