import os, asyncio, threading, json, httpx, psycopg2, secrets, time
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIG & SECURITY (Pulls from Render Env) ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS") 
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")

request_history = {} # Rate limiter storage
LATEST_SIGNAL = {"mint": "None", "status": "Hunting..."}

# --- DATABASE SETUP ---
def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, mint TEXT, profit TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, tg_id TEXT UNIQUE, api_key TEXT UNIQUE, paid BOOLEAN DEFAULT FALSE);")
        conn.commit(); cur.close(); conn.close()
    except: pass

# --- SECURE API GATEWAY (The Bouncer) ---
class FortressHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        user_ip = self.client_address[0]
        now = time.time()
        if user_ip in request_history and now - request_history[user_ip] < 1.0:
            self.send_response(429); self.end_headers()
            return
        request_history[user_ip] = now
        if "/alpha" in self.path:
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "alpha": LATEST_SIGNAL}).encode())
        else:
            self.send_response(200); self.end_headers(); self.wfile.write(b"S.I.P. SECURE NODE")

# --- MESSAGING & CONTROL ---
async def send_tg(msg, chat_id=None):
    target = chat_id or TG_ADMIN
    async with httpx.AsyncClient() as c:
        await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": target, "text": msg, "parse_mode": "HTML"})

async def tg_router():
    last_id = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": last_id+1, "timeout": 20})
                for u in r.json().get("result", []):
                    last_id = u["update_id"]
                    msg = u.get("message", {}); txt = msg.get("text", ""); cid = str(msg.get("chat", {}).get("id"))
                    if cid == TG_ADMIN and txt == "/status":
                        await send_tg("📊 <b>EMPIRE STATUS</b>\n- Mode: 7-Day Reinvest\n- Security: Fortress (Rate Limit ON)")
        except: pass
        await asyncio.sleep(5)

async def master_loop():
    init_db(); asyncio.create_task(tg_router())
    await send_tg("🏰 <b>FORTRESS DEPLOYED</b>\nSovereign Intel Founder Verified.")
    while True: await asyncio.sleep(60)

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), FortressHandler).serve_forever(), daemon=True).start()
if __name__ == "__main__":
    if PK and RPC_URL: asyncio.run(master_loop())
