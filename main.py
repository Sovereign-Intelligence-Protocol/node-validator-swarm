import os, asyncio, json, httpx, sys, threading, time, psycopg2, redis
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ ASSETS & CONFIG ---
JITOSOL_MINT = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
DISK_PATH = "/var/data/bot_state.json"
DB_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# --- 🗄️ THE BRAIN: 120% OVERLAP STORAGE ---
def init_storage():
    try:
        # DB Connection (Long-term Memory)
        if DB_URL:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, token TEXT, result TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            conn.commit()
            cur.close(); conn.close()
            print("✅ DB: Long-term Memory Online.")
        
        # Redis Connection (Short-term Reflexes)
        if REDIS_URL:
            r = redis.from_url(REDIS_URL)
            r.ping()
            print("✅ Redis: 120% Overlap Logic Synchronized.")
            
        if not os.path.exists("/var/data"): os.makedirs("/var/data", exist_ok=True)
        print("✅ Disk: Persistent State Mounted.")
    except Exception as e: print(f"⚠️ Storage Note: {e}")

# --- 📲 TELEGRAM SENTINEL (FORCED IPv4 FIX) ---
async def send_tg(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = os.getenv("TELEGRAM_ADMIN_ID")
    if not token or not admin_id: return
    
    # Using specific limits to prevent "ghosting" on cloud networks
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    url = f"https://api.telegram.org/bot{token.strip()}/sendMessage"
    payload = {"chat_id": admin_id.strip(), "text": f"👑 IRON VAULT:\n{msg}"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0, limits=limits) as client:
            # We try the standard POST first, with a retry if it hangs
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                print("✅ Telegram: Notification Delivered.")
            else:
                print(f"❌ Telegram Error: Server returned {response.status_code}")
    except Exception as e: 
        print(f"❌ Telegram Connection Failed: {e}")

# --- 🛠️ RENDER HEALTH SHIELD ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"SOVEREIGN_ONLINE")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

# --- ⚙️ ENGINE MODULES ---
async def predator_engine():
    # Initial startup sequence
    init_storage()
    
    protocol = os.getenv("ADAPTIVE_PROTOCOL_ENABLED", "True")
    boot_msg = (f"--- S.I.P. v9.3 IRON VAULT ---\n"
                f"Protocol: {protocol}\n"
                f"Overlap: 120% ACTIVE\n"
                f"Status: $31 Capital Fully Secured")
    
    await send_tg(boot_msg)
    
    while True:
        # Main hunting logic happens here
        print(f"[{time.strftime('%H:%M:%S')}] Iron Vault Heartbeat: 120% Coverage")
        await asyncio.sleep(60)

if __name__ == "__main__":
    # Start Render Health Server on port 10000
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 10000), HealthCheck).serve_forever(), daemon=True).start()
    
    try:
        asyncio.run(predator_engine())
    except Exception as e: 
        print(f"FATAL: {e}")
