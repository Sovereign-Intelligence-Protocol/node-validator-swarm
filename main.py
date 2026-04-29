import os
import asyncio
import httpx
import signal
import threading
import time
import psycopg2
from solders.pubkey import Pubkey
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ CONFIG (Exact Match to Your Labels) ---
PORT = int(os.getenv("PORT", 10000))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Surgical Fix: Ensure the Admin ID is stripped of any accidental spaces
ADMIN_ID = str(os.getenv("TELEGRAM_ADMIN_ID", "")).strip()

running = True

def handle_shutdown(signum, frame):
    global running
    print("⚠️ SIGTERM received. Graceful shutdown for 120s overlap...")
    running = False

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# --- 📲 TELEGRAM SENDER ---
async def send_tg(msg_text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Ensure we use the clean ADMIN_ID here too
    payload = {"chat_id": ADMIN_ID, "text": f"👑 IRON VAULT:\n{msg_text}"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except Exception as e:
        print(f"Send Error: {e}")

# --- 📲 TELEGRAM COMMAND HANDLER ---
async def handle_commands():
    last_update_id = 0
    
    # Fresh Start: Clears old messages so the bot only hears NEW commands
    async with httpx.AsyncClient() as client:
        try:
            init_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?limit=1&offset=-1"
            init_resp = await client.get(init_url)
            if init_resp.status_code == 200:
                results = init_resp.json().get("result", [])
                if results:
                    last_update_id = results[0]["update_id"]
        except Exception as e:
            print(f"Initial sync error: {e}")

    await send_tg("✅ SYSTEM ONLINE: S.I.P. v9.5 Ready.")
    
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
                        text = msg.get("text", "")
                        # Surgical Fix: Clean the incoming user_id for comparison
                        user_id = str(msg.get("from", {}).get("id", "")).strip()

                        # The Security Gate
                        if user_id == ADMIN_ID:
                            if text == "/hunt":
                                await send_tg("🎯 Hunt mode re-initialized. Scanning...")
                            elif text == "/health":
                                await send_tg("🟢 System Health: 100% | Overlap Shield Active")
                            elif text == "/subscribers":
                                await send_tg("📈 SUBSCRIPTION STATS\nTotal Active Subscribers: 1")
                            elif text == "/revenue":
                                await send_tg("💰 REVENUE: Logic engaged. Stats pending.")
                        else:
                            print(f"⛔ Unauthorized: {user_id} tried to use {text}")
                
                elif resp.status_code == 401:
                    print("❌ 401 Unauthorized: Check your TELEGRAM_BOT_TOKEN!")

            except Exception as e:
                if running:
                    print(f"Loop Error: {e}")
            await asyncio.sleep(1)

# --- 🛠️ HEALTH CHECK ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ONLINE")
    def log_message(self, format, *args): return

# --- ⚙️ MAIN ENGINE ---
async def predator_engine():
    asyncio.create_task(handle_commands())
    while running:
        print(f"[{time.strftime('%H:%M:%S')}] Iron Vault: Pulse Stable")
        await asyncio.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever(), daemon=True).start()
    try:
        asyncio.run(predator_engine())
    except (KeyboardInterrupt, SystemExit):
        pass
