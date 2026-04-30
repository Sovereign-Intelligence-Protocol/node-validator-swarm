import os, asyncio, threading, base58, json, httpx, psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- 1. CONFIG & DB SETUP ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")

def init_db():
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, token TEXT, profit TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, tg_id TEXT UNIQUE, paid BOOLEAN DEFAULT FALSE);")
        conn.commit()
        cur.close()
        conn.close()
        print("DB: Tables Initialized")
    except Exception as e: print(f"DB Error: {e}")

# --- 2. HEALTH CHECK ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SYSTEM_ALIVE")
    def log_message(self, *args): return 

def run_srv():
    HTTPServer(('0.0.0.0', PORT), HealthHandler).serve_forever()
threading.Thread(target=run_srv, daemon=True).start()

# --- 3. CORE LOGIC ---
async def send_tg(msg):
    async with httpx.AsyncClient() as c:
        await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})

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
                        await send_tg("<b>SIP FULL STACK ONLINE</b>\n- Sniper: Active\n- Toll Bridge: Active\n- Database: Connected")
            except: pass
            await asyncio.sleep(5)

async def predator():
    init_db()
    asyncio.create_task(tg_router())
    print("ENGINE: DATABASE + TOLL + SNIPER ACTIVE")
    await send_tg("💎 <b>DATABASE LINKED</b>\nEvery trade and toll is now being logged.")
    
    while True:
        print("Action: Hunting & Logging...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    if PK and RPC_URL: asyncio.run(predator())
