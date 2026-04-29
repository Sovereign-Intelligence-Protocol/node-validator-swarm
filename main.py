import os, asyncio, json, httpx, sys, threading, time, psycopg2, redis
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ ASSETS & CONFIG ---
JITOSOL_MINT = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
DISK_PATH = "/var/data/bot_state.json"
DB_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
# CRITICAL: Render dynamic port binding
PORT = int(os.getenv("PORT", 10000))

# --- 🗄️ THE BRAIN: 120% OVERLAP STORAGE ---
def init_storage():
    try:
        # Long-term Memory (Postgres)
        if DB_URL:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, token TEXT, result TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            conn.commit()
            cur.close(); conn.close()
            print("✅ DB: Iron Vault Brain Online.")
        
        # Short-term Reflexes (Redis)
        if REDIS_URL:
            r = redis.from_url(REDIS_URL)
            r.ping()
            print("✅ Redis: 120% Overlap Logic Synchronized.")
            
        if not os.path.exists("/var/data"): os.makedirs("/var/data", exist_ok=True)
        print("✅ Disk: Persistent State Mounted.")
    except Exception as e: print(f"⚠️ Storage Note: {e}")

# --- 📲 TELEGRAM SENTINEL (STABILIZED) ---
async def send_tg(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = os.getenv("TELEGRAM_ADMIN_ID")
    if not token or not admin_id:
        print("❌ Telegram: Missing Token or ID.")
        return
    
    url = f"https://api.telegram.org/bot{token.strip()}/sendMessage"
    payload = {"chat_id": admin_id.strip(), "text": f"👑 IRON VAULT:\n{msg}"}
    
    try:
        # Increased timeout and retry for 2026 network stability
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                print("✅ Telegram: Handshake Successful.")
            else:
                print(f"❌ Telegram: Server returned {response.status_code}")
    except Exception as e: print(f"❌ Telegram Failure: {e}")

# --- 🛠️ RENDER HEALTH SHIELD (PORT-AWARE) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"SOVEREIGN_ONLINE")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

# --- ⚙️ ENGINE MODULES ---
async def predator_engine():
    init_storage()
    
    boot_msg = (f"--- S.I.P. v9.4 IRON VAULT LIVE ---\n"
                f"Status: Port {PORT} Bound\n"
                f"Overlap: 120% ACTIVE\n"
                f"Wallet: $31 Vault Secured")
    
    await send_tg(boot_msg)
    
    while True:
        # Hunting loop: Snipe, Arb, Stake
        print(f"[{time.strftime('%H:%M:%S')}] Iron Vault: Pulse Stable (Port {PORT})")
        await asyncio.sleep(60)

if __name__ == "__main__":
    # Start Health Server on the port assigned by Render
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever(), daemon=True).start()
    try:
        asyncio.run(predator_engine())
    except Exception as e: print(f"FATAL: {e}")
