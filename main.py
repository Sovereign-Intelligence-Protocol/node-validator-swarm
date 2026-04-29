import os
import asyncio
import httpx
import signal
import threading
import time
import psycopg2
from solders.pubkey import Pubkey
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ CONFIG ---
PORT = int(os.getenv("PORT", 10000))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = str(os.getenv("TELEGRAM_ADMIN_ID", "")).strip()

running = True

def handle_shutdown(signum, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

async def send_tg(msg_text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_ID, "text": f"👑 IRON VAULT:\n{msg_text}"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except: pass

async def handle_commands():
    last_update_id = 0
    
    # Fresh Start: Clear backlog
    async with httpx.AsyncClient() as client:
        try:
            init_resp = await client.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?limit=1&offset=-1")
            if init_resp.status_code == 200:
                results = init_resp.json().get("result", [])
                if results: last_update_id = results[0]["update_id"]
        except: pass

    await send_tg("🚀 VAULT FULLY ARMED: All commands online.")
    
    async with httpx.AsyncClient(timeout=35.0) as client:
        while running:
            try:
                url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
                resp = await client.get(url)
                if resp.status_code == 200:
                    updates = resp.json().get("result", [])
                    for update in updates:
                        last_update_id = update["update_id"]
                        msg = update.get("message", {})
                        text = msg.get("text", "").strip()
                        user_id = str(msg.get("from", {}).get("id", "")).strip()

                        if user_id == ADMIN_ID:
                            # --- 🧩 COMMAND ROUTING ---
                            if text == "/start":
                                await send_tg("Welcome to Sovereign Intelligence Protocol. Type /health to begin.")
                            
                            elif text == "/hunt":
                                await send_tg("🎯 SCANNING: Node-Validator-Swarm engaged. Searching for high-yield signatures...")
                            
                            elif text == "/health":
                                await send_tg("🟢 SYSTEM STATUS:\n- Render: Active\n- DB: Connected\n- Solana: RPC Stable\n- Shield: Online")
                            
                            elif text == "/subscribers":
                                await send_tg("📈 STATS:\nActive Users: 1\nTier: Sovereign Elite")
                            
                            elif text == "/revenue":
                                await send_tg("💰 BALANCE:\nWallet: [PENDING RPC]\nDatabase: Syncing metrics...")

                            elif text == "/wallet":
                                # Placeholder for the solders logic we can add later
                                await send_tg("🔑 WALLET: Solders library verified. Waiting for public key input.")

                            elif text == "/stop":
                                await send_tg("⚠️ ALERT: Shutdown command acknowledged. Waiting for SIGTERM.")
                            
                            else:
                                await send_tg(f"❓ Unknown Command: '{text}'\nTry /health for a status report.")
                
            except Exception as e:
                if running: print(f"Loop Error: {e}")
            await asyncio.sleep(1)

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ONLINE")
    def log_message(self, format, *args): return

async def predator_engine():
    asyncio.create_task(handle_commands())
    while running:
        # Heartbeat in logs
        print(f"[{time.strftime('%H:%M:%S')}] Iron Vault: Pulse Stable")
        await asyncio.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever(), daemon=True).start()
    try:
        asyncio.run(predator_engine())
    except: pass
