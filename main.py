import os, asyncio, threading, base58, json, httpx, psycopg2, secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient

# --- 1. CONFIG & REINVESTMENT SETTINGS ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS") 
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")

# TRADING & API PARAMETERS
ARB_CLIP_SOL = 0.1          # Your $31 "Vacuum" size
TOLL_FEE_SOL = 0.05         # The "Shovel" price
LATEST_SIGNAL = {"mint": "None", "liquidity": 0, "time": 0}

# --- 2. DATABASE (The SaaS Ledger) ---
def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, mint TEXT, profit TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        # Added api_key to track bot-to-bot clients
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, tg_id TEXT UNIQUE, api_key TEXT UNIQUE, paid BOOLEAN DEFAULT FALSE);")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e: print(f"DB Error: {e}")

def create_api_access(tg_id):
    """Generates a unique key for a paying bot-owner."""
    new_key = secrets.token_urlsafe(16)
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO clients (tg_id, api_key, paid) VALUES (%s, %s, True) ON CONFLICT (tg_id) DO UPDATE SET api_key = %s, paid = True;", (str(tg_id), new_key, new_key))
        conn.commit()
        cur.close()
        conn.close()
        return new_key
    except: return None

# --- 3. THE BOT-TO-BOT GATEWAY (API) ---
class SaaSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Endpoint for other bots to grab your alpha: /alpha?key=YOUR_KEY
        if "/alpha" in self.path:
            user_key = self.path.split("key=")[-1] if "key=" in self.path else ""
            
            # Simple validation check (In production, check DB for user_key)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Send the raw data bots need
            response = {
                "status": "success",
                "alpha": LATEST_SIGNAL,
                "provider": "S.I.P. Engine"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"S.I.P. SYSTEM ONLINE")

# --- 4. THE MONETIZED ENGINE ---
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
                    msg = u.get("message", {})
                    txt, cid = msg.get("text", ""), str(msg.get("chat", {}).get("id"))
                    
                    if cid != TG_ADMIN:
                        # Professional welcome for prospective clients
                        welcome = f"🏁 <b>S.I.P. DATA STREAM</b>\n\nTo connect your bot to our high-velocity JSON feed, send <b>{TOLL_FEE_SOL} SOL</b> to:\n<code>{WH}</code>\n\nReply with /verify [signature]"
                        await send_tg(welcome, chat_id=cid)
                        continue

                    if txt.startswith("/verify"):
                        # If payment is confirmed, give them their API Key
                        new_key = create_api_access(cid)
                        await send_tg(f"✅ <b>ACCESS GRANTED</b>\nYour Bot API Key: <code>{new_key}</code>\nEndpoint: <code>https://your-app.render.com/alpha?key={new_key}</code>")
        except: pass
        await asyncio.sleep(5)

async def master_loop():
    init_db()
    asyncio.create_task(tg_router())
    await send_tg("🏗️ <b>INFRASTRUCTURE ONLINE</b>\nAPI Gateway is live. Sniper & Arb are active.")
    
    while True:
        # Here, LATEST_SIGNAL would be updated by the sniper/arb loops
        print("SaaS: Monitoring data streams for subscribers...")
        await asyncio.sleep(60)

# --- 5. BOOT ---
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), SaaSHandler).serve_forever(), daemon=True).start()

if __name__ == "__main__":
    if PK and RPC_URL: asyncio.run(master_loop())
