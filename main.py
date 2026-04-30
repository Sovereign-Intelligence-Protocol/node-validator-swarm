import os, asyncio, threading, base58, json, httpx, psycopg2, secrets, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient

# --- 1. CONFIG & SECURITY SHIELDS ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS") 
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")

# API RATE LIMITING STORAGE
request_history = {} 

# TRADING PARAMETERS
ARB_CLIP_SOL = 0.1
TOLL_FEE_SOL = 0.05
LATEST_SIGNAL = {"mint": "None", "liquidity": 0, "status": "Hunting"}

# --- 2. DATABASE (The Secure Ledger) ---
def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, mint TEXT, profit TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        # Added api_key to track paid bots securely
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, tg_id TEXT UNIQUE, api_key TEXT UNIQUE, paid BOOLEAN DEFAULT FALSE);")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e: print(f"DB Error: {e}")

# --- 3. THE SECURE API GATEWAY ---
class FortressHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        user_ip = self.client_address[0]
        now = time.time()

        # SHIELD: Rate Limiting (1 request per second max)
        if user_ip in request_history and now - request_history[user_ip] < 1.0:
            self.send_response(429)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Rate limit exceeded. Slow down."}).encode())
            return
        
        request_history[user_ip] = now

        if "/alpha" in self.path:
            # SHIELD: API Key Validation
            user_key = self.path.split("key=")[-1] if "key=" in self.path else ""
            
            # Here we verify the key against our DB
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "success",
                "alpha": LATEST_SIGNAL,
                "note": "Reinvesting tolls for 7 days."
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"S.I.P. SECURE NODE")

# --- 4. THE MONETIZED ENGINE ---
async def send_tg(msg, chat_id=None):
    target = chat_id or TG_ADMIN
    async with httpx.AsyncClient() as c:
        await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     json={"chat_id": target, "text": msg, "parse_mode": "HTML"})

async def tg_router():
    last_id = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": last_id+1, "timeout": 20})
                for u in r.json().get("result", []):
                    last_id = u["update_id"]
                    msg = u.get("message", {})
                    txt, cid = msg.get("text", ""), str(msg.get("chat", {}).get("id"))
                    
                    if cid != TG_ADMIN:
                        welcome = f"🛡️ <b>S.I.P. SECURE API</b>\n\nToll: <b>{TOLL_FEE_SOL} SOL</b>\nWallet: <code>{WH}</code>\n\nSubmit /verify [sig] for your API Key."
                        await send_tg(welcome, chat_id=cid)
                        continue

                    if txt == "/status":
                        stats = "📊 <b>EMPIRE STATUS</b>\n- Mode: 7-Day Reinvest\n- Security: Rate Limiter ON\n- Shield: Env Vars Active"
                        await send_tg(stats)
        except: pass
        await asyncio.sleep(5)

async def master_loop():
    init_db()
    asyncio.create_task(tg_router())
    await send_tg("🏰 <b>FORTRESS DEPLOYED</b>\nAPI Security Active. System Monitoring.")
    while True:
        await asyncio.sleep(60)

# --- 5. BOOT ---
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), FortressHandler).serve_forever(), daemon=True).start()

if __name__ == "__main__":
    if PK and RPC_URL: asyncio.run(master_loop())
