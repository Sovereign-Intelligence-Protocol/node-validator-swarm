import os, time, asyncio, threading, sys, signal
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- CONFIG & SYSTEM STATE ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT, STILL_RUNNING = int(os.environ.get("PORT", 10000)), True

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# 120-SECOND OVERLAP HANDLER
def exit_gate(signum, frame):
    global STILL_RUNNING
    log("!!! SIGTERM: KILLING SCANNER & STARTING 120S LAPSE !!!")
    STILL_RUNNING = False
    time.sleep(120) 
    os._exit(0)

signal.signal(signal.SIGTERM, exit_gate)

async def scan_loop():
    log(f"==> OMNICORE V7.0 ONLINE: {RPC}")
    async with AsyncClient(RPC) as client:
        while STILL_RUNNING:
            try:
                # 2-SECOND SCAN RHYTHM
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                # ADD JITO / JUPITER / TELEGRAM LOGIC HERE
                await asyncio.sleep(2) 
            except Exception as e:
                log(f"RPC ERROR: {e}")
                await asyncio.sleep(5)

# --- INFRASTRUCTURE ---
app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V7.0_STABLE", 200

if __name__ == "__main__":
    # START BACKGROUND ENGINE
    threading.Thread(target=lambda: asyncio.run(scan_loop()), daemon=True).start()
    log(f"==> WEB SERVER PORT: {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
