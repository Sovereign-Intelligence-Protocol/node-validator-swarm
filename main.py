import os, asyncio, threading, base58, json, httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- 1. EMERGENCY HEALTH CHECK (FIRST PRIORITY) ---
PORT = int(os.environ.get("PORT", 10000))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SIP_STATUS_OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args): return

def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()

# Start health check in background immediately
threading.Thread(target=run_health_server, daemon=True).start()

# --- 2. CONFIGURATION ---
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS")
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")
TOLL = os.environ.get("JITO_TIP_AMOUNT", "0.05")

# --- 3. TELEGRAM LOGIC ---
async def send_tg(msg):
    if not TG_TOKEN or not TG_ADMIN: return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"}
            )
        except Exception:
            pass

async def tg_router():
    """Simple Telegram Listener"""
    last_id = 0
    async with httpx.AsyncClient() as client:
        while True:
            try:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
                r = await client.get(url, params={"offset": last_id + 1, "timeout": 10})
                updates = r.json().get("result", [])
                for u in updates:
                    last_id = u["update_id"]
                    msg = u.get("message", {})
                    if str(msg.get("chat", {}).get("id")) == TG_ADMIN:
                        txt = msg.get("text", "").lower()
                        if txt == "/status":
                            await send_tg(f"<b>SIP SYSTEM ONLINE</b>\nWallet: <code>{WH}</code>")
            except Exception:
                await asyncio.sleep(5)
            await asyncio.sleep(2)

# --- 4. THE PREDATOR ENGINE ---
async def predator():
    # Start Telegram Listener
    asyncio.create_task(tg_router())
    
    # Verify Wallet
    try:
        payer = Keypair.from_bytes(base58.b58decode(PK))
        await send_tg(f"🚀 <b>SIP ENGINE ACTIVATED</b>\n$31 War-Chest Loaded.")
    except Exception as e:
        print(f"Keypair Error: {e}")
        return

    while True:
        try:
            # This is where the hunt happens
            print("Action: Scanning for targets...")
            await asyncio.sleep(120)
        except Exception as e:
            await send_tg(f"⚠️ <b>System Alert:</b> {e}")
            await asyncio.sleep(10)

async def main():
    if not PK:
        print("CRITICAL: PRIVATE_KEY is missing in Environment Variables!")
        return
    await predator()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
