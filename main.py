import os, time, asyncio, threading, sys, signal
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- SYSTEM STATE ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PORT = int(os.environ.get("PORT", 10000))
STILL_RUNNING = True 

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# --- THE 120-SECOND MANUAL OVERLAP ---
def emergency_shutdown(signum, frame):
    global STILL_RUNNING
    log("!!! SIGTERM DETECTED: KILLING OLD SCANNER IMMEDIATELY !!!")
    STILL_RUNNING = False  # This stops the 2-second loop instantly
    
    log("!!! INITIATING MANUAL 120s TIME LAPSE !!!")
    # This keeps the old process alive but silent for 2 minutes
    time.sleep(120) 
    
    log("!!! LAPSE EXPIRED: EXITING !!!")
    os._exit(0) # Force exit to bypass any Flask cleanup hangs

# Register shutdown handler immediately at boot
signal.signal(signal.SIGTERM, emergency_shutdown)

async def scan_loop():
    log(f"==> BOOTING ENGINE: {RPC}")
    async with AsyncClient(RPC) as client:
        while STILL_RUNNING:
            try:
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                await asyncio.sleep(2)
            except Exception as e:
                log(f"RPC ERROR: {e}")
                await asyncio.sleep(5)
        log("==> SCANNER DISENGAGED. OLD INSTANCE NOW IN 120s IDLE PHASE.")

# --- WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V6.9_STABLE", 200

if __name__ == "__main__":
    # Start background engine
    t = threading.Thread(target=lambda: asyncio.run(scan_loop()), daemon=True)
    t.start()
    
    log(f"==> WEB SERVER ACTIVE ON PORT {PORT}")
    # MUST have use_reloader=False for the 120s lapse to work
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
