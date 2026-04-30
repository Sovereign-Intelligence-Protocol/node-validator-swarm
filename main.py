import os, time, asyncio, threading, sys, signal
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- CONFIG & STATE ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PORT = int(os.environ.get("PORT", 10000))
SHUTTING_DOWN = False

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# THE 120-SECOND OVERLAP HANDLER
def handle_exit(signum, frame):
    global SHUTTING_DOWN
    log("!!! SIGTERM RECEIVED: STOPPING SCANNER & HOLDING FOR 120S OVERLAP !!!")
    SHUTTING_DOWN = True  # Immediately stops the scanning loop
    time.sleep(120)       # Keeps the process alive but idle for the overlap
    log("!!! OVERLAP EXPIRED: EXITING !!!")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)

async def scan_loop():
    log(f"==> CONNECTING: {RPC}")
    async with AsyncClient(RPC) as client:
        while not SHUTTING_DOWN:
            try:
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                await asyncio.sleep(2)
            except Exception as e:
                log(f"SCAN ERROR: {e}")
                await asyncio.sleep(5)
        log("==> SCANNER KILLED: STANDING BY DURING TRANSITION...")

# --- RENDER INFRASTRUCTURE ---
app = Flask(__name__)
@app.route('/')
def health(): return {"status": "SHUTTING_DOWN" if SHUTTING_DOWN else "LIVE"}, 200

if __name__ == "__main__":
    log("==> INITIALIZING S.I.P. OMNICORE...")
    # Start loop in background
    threading.Thread(target=lambda: asyncio.run(scan_loop()), daemon=True).start()
    log(f"==> BINDING TO PORT {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
