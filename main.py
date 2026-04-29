import os, asyncio, json, httpx, sys, threading, time
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

# --- 📲 TELEGRAM SENTINEL ---
async def send_tg(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = os.getenv("TELEGRAM_ADMIN_ID")
    if not token or not admin_id: return
    try:
        url = f"https://api.telegram.org/bot{token.strip()}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={"chat_id": admin_id.strip(), "text": f"🛡️ S.I.P. Sentinel:\n{message}"})
    except Exception as e: print(f"TG Error: {e}")

# --- 🛠️ RENDER SURVIVAL CIRCUIT (FIXED FOR 501 ERRORS) ---
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SENTINEL_ONLINE")

    def do_HEAD(self):
        # This handles Render's 'HEAD' check to prevent 501 Unsupported Method errors
        self.send_response(200)
        self.end_headers()

# --- 🛡️ SECURE KEY LOADER ---
def load_key(env, is_pub=False):
    val = os.getenv(env, "").strip().replace('"', '').replace("'", "")
    if not val: return None
    try:
        return Pubkey.from_string(val) if is_pub else Keypair.from_base58_string(val)
    except: return None

# --- ⚙️ CONFIGURATION ---
RPC_URL = os.getenv("RPC_URL")
WALLET = load_key("SOLANA_WALLET_ADDRESS", True)
SIGNER = load_key("PRIVATE_KEY")
LIVE = os.getenv("LIVE_TRADING", "false").lower() == "true"

# DYNAMIC TIP FIX: Handles '0.001' (SOL) or '1000000' (Lamports)
raw_tip = os.getenv("JITO_TIP_AMOUNT", "1000000")
try:
    if "." in raw_tip:
        JITO_TIP = int(float(raw_tip) * 1_000_000_000)
    else:
        JITO_TIP = int(raw_tip)
except:
    JITO_TIP = 1000000

async def predator_engine():
    # Fresh timestamp to prove it's a new session
    start_time = time.strftime('%H:%M:%S')
    msg = f"--- S.I.P. v8.9 IRONCLAD ---\nTime: {start_time}\nStatus: {'LIVE HUNT' if LIVE else 'SIM'}\nTip: {JITO_TIP} Lamports"
    print(msg); await send_tg(msg)
    
    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        while True:
            # Core Hunting Logic (RugCheck, Simulation, Jito Strike)
            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] Sentinel Heartbeat: Active")
            await asyncio.sleep(60)

if __name__ == "__main__":
    # Start the Survival Server with HEAD support
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 10000), HealthCheck).serve_forever(), daemon=True).start()
    try:
        asyncio.run(predator_engine())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"FATAL CRASH: {e}")
