import os, time, asyncio, threading, sys, signal, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- CONFIG ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT, ACTIVE = int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN:
        async with httpx.AsyncClient() as c:
            await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": "@me", "text": m})

def handoff(s, f):
    global ACTIVE
    log("!!! SIGTERM RECEIVED: 120S TIME LOOP START !!!")
    ACTIVE = False
    time.sleep(120)  # YOUR ESSENTIAL 120S TIME LOOP
    os._exit(0)

signal.signal(signal.SIGTERM, handoff)

async def core_engine():
    log(f"==> OMNICORE LIVE: {RPC}")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                res = await client.get_slot()
                slot = res.value
                log(f"SCANNING SLOT: {slot}") #
                
                # --- ACTUAL TRADING LOGIC ONLY ---
                # Place your production Jupiter/Jito execution here
                
                await asyncio.sleep(2) # 2s SWEET SPOT
            except Exception as e:
                log(f"CORE ERROR: {e}")
                await asyncio.sleep(5)

app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V7.0_STABLE", 200

if __name__ == "__main__":
    # START BACKGROUND ENGINE
    threading.Thread(target=lambda: asyncio.run(core_engine()), daemon=True).start()
    log(f"==> SERVER STARTING ON PORT {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
