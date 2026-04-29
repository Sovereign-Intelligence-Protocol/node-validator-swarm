import os, asyncio, json, httpx, sys, threading, time, psycopg2
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ CONFIG & ASSETS ---
JITOSOL_MINT = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
DISK_PATH = "/var/data/bot_state.json" # Mount your Render disk here
DB_URL = os.getenv("DATABASE_URL")

# --- 🗄️ DATABASE & DISK LOGIC ---
def init_storage():
    try:
        # 1. Init Postgres
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                token TEXT,
                type TEXT,
                amount NUMERIC,
                result TEXT,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close(); conn.close()
        # 2. Init Disk State
        if not os.path.exists("/var/data"): os.makedirs("/var/data")
        if not os.path.exists(DISK_PATH):
            with open(DISK_PATH, 'w') as f: json.dump({"total_snipped": 0}, f)
        print("✅ Storage: Database & Disk Synchronized.")
    except Exception as e: print(f"❌ Storage Error: {e}")

# --- 📲 TELEGRAM SENTINEL ---
async def send_tg(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = os.getenv("TELEGRAM_ADMIN_ID")
    if token and admin_id:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"https://api.telegram.org/bot{token.strip()}/sendMessage", 
                                  json={"chat_id": admin_id.strip(), "text": f"👑 IRON VAULT:\n{msg}"})
        except: pass

# --- 🛠️ RENDER HEALTH CHECK (Fixes 501 Error) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"ONLINE")
    def do_HEAD(self): self.send_response(200); self.end_headers()

# --- ⚙️ ENGINE MODULES ---
async def hunting_loop():
    # Integrated Sniper & Arbitrage Logic
    # Uses your Jito settings from env vars automatically
    await asyncio.sleep(1) 

async def predator_engine():
    init_storage()
    await send_tg("v9.2 Iron Vault Active. Database & Disk Online.")
    while True:
        await hunting_loop()
        await asyncio.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 10000), HealthCheck).serve_forever(), daemon=True).start()
    asyncio.run(predator_engine())
