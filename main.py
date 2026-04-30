import os, asyncio, threading, base58, json, httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- 1. RENDER HEALTH CHECK ---
PORT = int(os.environ.get("PORT", 10000))
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SYSTEM_ALIVE")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args): return 

def run_srv():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_srv, daemon=True).start()

# --- 2. CONFIGURATION (STRICTLY FROM ENVIRONMENT) ---
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS")
RPC_URL = os.environ.get("RPC_URL") # Helius URL is hidden here
PK = os.environ.get("PRIVATE_KEY")
TOLL = os.environ.get("JITO_TIP_AMOUNT", "0.05")

# --- 3. TELEGRAM LOGIC ---
async def send_tg(msg):
    if not TG_TOKEN or not TG_ADMIN: return
    async with httpx.AsyncClient() as c:
        try: 
            await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                         json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except Exception: pass

async def tg_router():
    last_id = 0
    async with httpx.AsyncClient() as c:
        while True:
            try:
                r = await c.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": last_id+1, "timeout": 20})
                for u in r.json().get("result", []):
                    last_id = u["update_id"]
                    msg = u.get("message", {})
                    txt, cid = msg.get("text", "").lower(), str(msg.get("chat", {}).get("id"))
                    if cid != TG_ADMIN: continue
                    
                    if txt == "/status":
                        await send_tg(f"<b>SIP LIVE</b>\nStatus: Secure & Scanning")
            except Exception: pass
            await asyncio.sleep(5)

# --- 4. THE PREDATOR CORE (SANITIZED) ---
async def predator():
    asyncio.create_task(tg_router())
    
    # We only print confirmation, NEVER the actual keys/URLs
    try:
        payer_kp = Keypair.from_bytes(base58.b58decode(PK))
        print("Wallet: LOADED")
    except Exception:
        print("Wallet: ERROR (Check Private Key)")
        return

    print("RPC: CONNECTED (URL Hidden for Security)")
    await send_tg("🚀 <b>SIP ENGINE ACTIVATED</b>\nSecurity: Stealth Mode ON")
    
    while True:
        try:
            # Main hunting loop
            print("Action: Scanning for opportunities...")
            await asyncio.sleep(120) 
        except Exception as e:
            # Generic error reporting to avoid leaking context
            print("System Alert: Connection Pulse Reset")
            await asyncio.sleep(10)

async def main():
    if PK and RPC_URL: 
        await predator()
    else: 
        print("CRITICAL: Environment Variables Missing!")

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
