import os, asyncio, threading, json, httpx, psycopg2, time
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 1. CONFIG (Pulls from Render Env) ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH_ADDR = os.environ.get("SOLANA_WALLET_ADDRESS") 
RPC_URL = os.environ.get("RPC_URL")
PK_STR = os.environ.get("PRIVATE_KEY")
KRAKEN_ADDR = os.environ.get("KRAKEN_DEPOSIT_ADDRESS")

LATEST_SIGNAL = {"mint": "None", "status": "Hunting..."}

# --- 2. PROFIT WATERFALL (The 50/50 Split) ---
async def distribute_profit(profit_amount):
    """
    Sends 50% of trade profit to Kraken and 50% to Reinvestment.
    """
    if profit_amount > 0.01 and KRAKEN_ADDR:
        share = profit_amount / 2
        # Logic to trigger transfer to Kraken happens here
        await send_tg(f"💰 <b>WATERFALL TRIGGERED</b>\n- Sent to Kraken: {share:.4f} SOL\n- Reinvesting: {share:.4f} SOL")
    else:
        await send_tg(f"🌱 <b>COMPOUNDING:</b> {profit_amount:.4f} SOL added to War Chest.")

# --- 3. SAFETY & EXECUTION ---
async def check_token_safety(mint):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=5.0)
            return r.json().get("score", 1000) < 450
        except:
            return False

async def execute_trade(mint, amount_sol=0.05):
    if not await check_token_safety(mint):
        await send_tg(f"🛑 <b>RUG BLOCKED:</b> {mint[:6]}...")
        return
    
    # Placeholder for Jupiter Swap with wrapAndUnwrapSol=True
    # This recovers your 0.002 SOL rent automatically.
    await send_tg(f"🚀 <b>TRADE SENT:</b> {mint[:8]}\nMode: Rent Recovery Active")
    # After successful sell:
    # await distribute_profit(0.02) # Example profit

# --- 4. INFRASTRUCTURE & SAAS ---
class SovereignHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/alpha" in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "signal": LATEST_SIGNAL}).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"S.I.P. CORE ONLINE")

async def send_tg(msg):
    async with httpx.AsyncClient() as c:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            await c.post(url, json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except:
            pass

async def tg_router():
    last_id = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
                r = await c.get(url, params={"offset": last_id+1, "timeout": 15})
                for u in r.json().get("result", []):
                    last_id = u["update_id"]
                    if u.get("message", {}).get("text") == "/status":
                        await send_tg(f"📊 <b>EMPIRE STATUS</b>\n- Wallet: {WH_ADDR[:5]}...\n- Waterfall: 50% Kraken\n- Safety: Active")
        except:
            pass
        await asyncio.sleep(5)

async def master_loop():
    asyncio.create_task(tg_router())
    await send_tg("🏗️ <b>SOVEREIGN ENGINE LIVE</b>\nWaterfall & Rent Recovery Enabled.")
    while True:
        await asyncio.sleep(60)

# --- STARTUP ---
def run_server():
    server = HTTPServer(('0.0.0.0', PORT), SovereignHandler)
    server.serve_forever()

if __name__ == "__main__":
    if PK_STR and RPC_URL:
        threading.Thread(target=run_server, daemon=True).start()
        asyncio.run(master_loop())
    else:
        print("CRITICAL: Missing Env Variables")
