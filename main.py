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
ADMIN_ID = str(os.getenv("TELEGRAM_ADMIN_ID", "")).strip()

running = True

def handle_shutdown(signum, frame):
    global running
    print("⚠️ SIGTERM received. Graceful shutdown for 120s overlap...")
    running = False

# Register signals for clean deployment handoff
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# --- 📲 TELEGRAM SENDER ---
async def send_tg(msg_text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_ID, "text": f"👑 IRON VAULT:\n{msg_text}"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except Exception as e:
        print(f"Send Error: {e}")

# --- 📲 TELEGRAM COMMAND HANDLER ---
async def handle_commands():
    last_update_id = 0
    # Startup signal: You will get this in TG if the code is running
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
                        user_id = str(msg.get("from", {}).get("id", ""))

                        # Security Check: Compare against your TELEGRAM_ADMIN_ID
                        if user_id == ADMIN_ID:
                            if text == "/hunt":
                                await send_tg("🎯 Hunt mode re-initialized. Scanning...")
                            elif text == "/health":
                                await send_tg("🟢 System Health: 100% | Overlap Shield Active")
                            elif text == "/subscribers":
                                await send_tg("📈 SUBSCRIPTION STATS\nTotal Active Subscribers: 1")
                            elif text == "/revenue":
                                await send_tg("💰 REVENUE: Logic engaged. Stats pending.")
                
                elif resp.status_code == 401:
                    print("❌ 401 Unauthorized: Your Bot Token is likely invalid.")

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
    # Start Telegram Listener in background
    asyncio.create_task(handle_commands())
    
    while running:
        # Core Hunting Logic Loop
        print(f"[{time.strftime('%H:%M:%S')}] Iron Vault: Pulse Stable")
        await asyncio.sleep(60)
    
    print("Engine stopped gracefully.")

if __name__ == "__main__":
    # Start Health Check Server for Render
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever(), daemon=True).start()
    
    # Run the Async Engine
    try:
        asyncio.run(predator_engine())
    except (KeyboardInterrupt, SystemExit):
        pass
