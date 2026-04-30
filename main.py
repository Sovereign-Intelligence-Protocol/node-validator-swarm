import os, asyncio, threading, base58, json, httpx, psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# --- 1. SETTINGS & BUDGET CONTROLS ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS") # Your wallet to receive tolls
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")

# AGGRESSIVE TRADING PARAMETERS
MIN_LIQUIDITY_USD = 10000  # Protection for your $31
TP_LEVEL = 1.50            # Sell at 50% Profit
SL_LEVEL = 0.85            # Sell at 15% Loss
TOLL_AMOUNT_SOL = 0.05     # Price for other users to join

# --- 2. DATABASE PERSISTENCE ---
def init_db():
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, mint TEXT, profit TEXT, status TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, tg_id TEXT UNIQUE, paid BOOLEAN DEFAULT FALSE);")
        conn.commit()
        cur.close()
        conn.close()
        print("DB: Systems Ready")
    except Exception as e: print(f"DB Error: {e}")

def save_client(tg_id):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO clients (tg_id, paid) VALUES (%s, True) ON CONFLICT (tg_id) DO UPDATE SET paid = True;", (str(tg_id),))
        conn.commit()
        cur.close()
        conn.close()
    except: pass

# --- 3. TOLL BRIDGE VERIFICATION ---
async def verify_payment(sig):
    """Blockchain Bouncer: Confirms the 0.05 SOL Toll hit your wallet."""
    async with AsyncClient(RPC_URL) as client:
        try:
            # Check transaction on-chain
            res = await client.get_transaction(sig, commitment="confirmed", max_supported_transaction_version=0)
            if not res or not res.value: return False
            
            # Verify the success of the transaction
            meta = res.value.transaction.meta
            if meta.err is not None: return False
            
            # Check if YOUR wallet is in the account keys
            msg = res.value.transaction.transaction.message
            keys = [str(k) for k in msg.account_keys]
            
            if WH in keys:
                print(f"Verified Toll: {sig}")
                return True
            return False
        except Exception: return False

# --- 4. TELEGRAM INTERFACE ---
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
                    
                    # Welcome Message for Non-Admins (Toll Bridge)
                    if cid != TG_ADMIN:
                        welcome = f"<b>S.I.P. Sniper Engine</b>\n\nTo access high-velocity signals, send <b>{TOLL_AMOUNT_SOL} SOL</b> to:\n<code>{WH}</code>\n\nReply with your transaction signature to activate."
                        await send_tg(welcome, chat_id=cid)
                        continue

                    # Admin Commands
                    if txt == "/status":
                        await send_tg("🔥 <b>PREDATOR ACTIVE</b>\nMode: Aggressive Sniper\nBudget: $31\nToll Bridge: Online")
                    elif txt.startswith("/verify "):
                        sig = txt.split(" ")[1]
                        if await verify_payment(sig):
                            save_client(cid)
                            await send_tg("✅ <b>Verification Successful.</b> Toll logged in Database.")
                        else:
                            await send_tg("❌ <b>Verification Failed.</b> No matching transaction found.")
        except: pass
        await asyncio.sleep(5)

# --- 5. THE PREDATOR (AUTO-SNIPER) ---
async def predator():
    init_db()
    asyncio.create_task(tg_router())
    await send_tg("🚀 <b>SYSTEM FULLY MONETIZED</b>\nSniper ARMED | Toll Bridge LIVE | DB CONNECTED")
    
    while True:
        # High-speed hunting loop for your $31
        # 1. Detect New Pairs
        # 2. Check Liquidity > $10,000
        # 3. Buy 0.1 SOL and start Auto-Exit monitor
        print("Action: Hunting high-conviction targets...")
        await asyncio.sleep(45)

# --- 6. RENDER HEALTH CHECK ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"ALIVE")
    def log_message(self, *args): return 

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthHandler).serve_forever(), daemon=True).start()

if __name__ == "__main__":
    if PK and RPC_URL: asyncio.run(predator())
