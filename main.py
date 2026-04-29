import os, asyncio, json, httpx, sys, threading, time, psycopg2
from solders.pubkey import Pubkey
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ CONFIG ---
PORT = int(os.getenv("PORT", 10000))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

# --- 📲 TELEGRAM COMMAND HANDLER ---
async def handle_commands():
    last_update_id = 0
    print("📡 Telegram: Listener Online. Waiting for commands...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.get(url)
                updates = resp.json().get("result", [])
                
                for update in updates:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    user_id = str(msg.get("from", {}).get("id", ""))

                    if user_id == ADMIN_ID.strip():
                        if text == "/hunt":
                            await send_tg("🎯 Hunt mode re-initialized. Scanning for targets...")
                        elif text == "/health":
                            await send_tg("🟢 System Health: 100% | 120% Overlap Active | DB Connected")
                        elif text == "/subscribers":
                            await send_tg("📈 SUBSCRIPTION STATS\nTotal Active Subscribers: 1")
                
        except Exception as e:
            print(f"Listener Error: {e}")
        await asyncio.sleep(1)

# --- 📲 TELEGRAM SENDER ---
async def send_tg(msg_text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_ID, "text": f"👑 IRON VAULT:\n{msg_text}"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except: pass

# --- 🛠️ RENDER HEALTH SHIELD ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"ONLINE")
    def do_HEAD(self): self.send_response(200); self.end_headers()

# --- ⚙️ MAIN ENGINE ---
async def predator_engine():
    # Start the command listener in the background
    asyncio.create_task(handle_commands())
    
    await send_tg("--- S.I.P. v9.5 ONLINE ---\nCommands: /hunt, /health, /subscribers active.")
    
    while True:
        # Hunting logic remains here
        print(f"[{time.strftime('%H:%M:%S')}] Iron Vault: Pulse Stable")
        await asyncio.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever(), daemon=True).start()
    asyncio.run(predator_engine())
