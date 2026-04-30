import os, time, asyncio, threading, sys, signal
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- SYSTEM CONFIG ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PORT = int(os.environ.get("PORT", 10000))
SCAN_ACTIVE = True 

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# --- THE 120-SECOND MANUAL TIME LAPSE ---
def handle_handoff(signum, frame):
    global SCAN_ACTIVE
    log("!!! RENDER SIGNAL: KILLING SCANNER IMMEDIATELY !!!")
    SCAN_ACTIVE = False  # Instantly stops double-trading/scanning
    
    log("!!! STARTING MANUAL 120s TIME LAPSE FOR DEPLOYMENT OVERLAP !!!")
    time.sleep(120)  # The requested manual lapse
    
    log("!!! LAPSE COMPLETE: TERMINATING OLD PROCESS !!!")
    sys.exit(0)

# Register the handoff signal
signal.signal(signal.SIGTERM, handle_handoff)

async def scan_loop():
    log(f"==> BOOTING SCANNER: {RPC}")
    async with AsyncClient(RPC) as client:
        while SCAN_ACTIVE:
            try:
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                await asyncio.sleep(2)
            except Exception as e:
                log(f"RPC ERROR: {e}")
                await asyncio.sleep(5)
        log("==> SCANNER DISENGAGED. STANDING BY FOR HANDOFF WINDOW.")

# --- INFRASTRUCTURE ---
app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V6.8_ACTIVE", 200

if __name__ == "__main__":
    # Launch logic in background
    threading.Thread(target=lambda: asyncio.run(scan_loop()), daemon=True).start()
    
    log(f"==> WEB SERVER STARTING ON PORT {PORT}")
    # use_reloader=False is required for signal.signal to work properly
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
