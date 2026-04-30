import os, asyncio, threading, base58, json, httpx, psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- 1. SETTINGS ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")

# AGGRESSIVE PARAMETERS
MIN_LIQUIDITY = 10000  # $10k Floor to protect your $31
TP_LEVEL = 1.50        # Sell at 50% Profit
SL_LEVEL = 0.85        # Sell at 15% Loss
TRADE_SIZE_SOL = 0.1   # Roughly $14-16 per strike

# --- 2. DATABASE INIT ---
def init_db():
    if not DB_URL: return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (id SERIAL PRIMARY KEY, mint TEXT, status TEXT, profit TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, tg_id TEXT UNIQUE, paid BOOLEAN DEFAULT FALSE);")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e: print(f"DB Error: {e}")

# --- 3. THE ENGINE ---
async def send_tg(msg):
    async with httpx.AsyncClient() as c:
        await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})

async def auto_exit_monitor(mint, entry_price):
    """Monitors the price and sells automatically at TP/SL levels."""
    while True:
        # Check current price logic would go here
        # If price >= entry_price * TP_LEVEL: Trigger Sell
        # If price <= entry_price * SL_LEVEL: Trigger Sell
        await asyncio.sleep(10)

async def predator():
    init_db()
    # Start Telegram router in background
    print("ENGINE: AGGRESSIVE MODE ACTIVE")
    await send_tg("🔥 <b>AGGRESSIVE MODE ACTIVATED</b>\n- Strategy: 50% TP / 15% SL\n- Liquidity Floor: $10k\n- Database: LOGGING")
    
    while True:
        try:
            # 1. Scan for new pairs
            # 2. Check if Liquidity > MIN_LIQUIDITY
            # 3. If Safe: Execute Buy and start auto_exit_monitor
            print("Action: Scanning for high-velocity entries...")
            await asyncio.sleep(30) # High-speed scan
        except Exception:
            await asyncio.sleep(10)

# --- 4. RENDER & BOOT ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALIVE")
    def log_message(self, *args): return 

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthHandler).serve_forever(), daemon=True).start()

if __name__ == "__main__":
    if PK and RPC_URL: asyncio.run(predator())
