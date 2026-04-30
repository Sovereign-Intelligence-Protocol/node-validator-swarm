import os, time, asyncio, threading, sys, signal
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- CONFIG & OVERLAP ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PORT = int(os.environ.get("PORT", 10000))
IS_ALIVE = True

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# THE 120-SECOND OVERLAP LOGIC
def start_overlap_delay(signum, frame):
    global IS_ALIVE
    log("!!! RENDER SIGNAL DETECTED: STARTING 120s OVERLAP DELAY !!!")
    IS_ALIVE = False  # Stops the scanner logic immediately
    
    # This manually holds the process open so the old and new versions overlap
    time.sleep(120) 
    
    log("!!! 120s OVERLAP COMPLETE: TERMINATING OLD INSTANCE !!!")
    sys.exit(0)

# Listen for Render's shutdown signal (SIGTERM)
signal.signal(signal.SIGTERM, start_overlap_delay)

async def scan_loop():
    log(f"==> SCANNER INITIALIZED: {RPC}")
    async with AsyncClient(RPC) as client:
        while IS_ALIVE:
            try:
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                await asyncio.sleep(2)
            except Exception as e:
                log(f"SCAN ERROR: {e}")
                await asyncio.sleep(5)
        log("==> SCANNER THREAD STOPPED. HOLDING PROCESS...")

# --- RENDER INFRASTRUCTURE ---
app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V6.6_RUNNING", 200

if __name__ == "__main__":
    log("==> BOOTING S.I.P. OMNICORE...")
    # Start the background scan
    threading.Thread(target=lambda: asyncio.run(scan_loop()), daemon=True).start()
    
    log(f"==> WEB SERVER ONLINE ON PORT {PORT}")
    # debug=False and use_reloader=False are mandatory for signal handling
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
