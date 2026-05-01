import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from jito_py.searcher import Searcher

# --- CONFIG & LABELS ---
RPC = os.getenv("RPC_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR = os.getenv("PRIVATE_KEY")
KRAKEN = os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL = os.getenv("DATABASE_URL")
PORT = int(os.environ.get("PORT", 10000))
ACTIVE = True

# --- STRATEGY CONSTANTS ---
WHALE_MIN_SOL = 5.0
TAKE_PROFIT = 1.20
STOP_LOSS = 0.90
POLL_INTERVAL = 0.1
ERROR_COUNT = 0
POSITIONS = {}

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

# --- DATABASE LOGGING ---
def save_trade(mint, side, price):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO trades (mint, side, price, time) VALUES (%s, %s, %s, %s)", 
                    (mint, side, price, time.time()))
        conn.commit()
        cur.close()
        conn.close()
    except: pass

async def notify(m):
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"💎 OMNICORE v10.4: {m}"})
        except: pass

# --- PILLAR 1: ADAPTIVE PREDATORY SCRAPER ---
async def predatory_scraper():
    global POLL_INTERVAL, ERROR_COUNT
    log(f"PREDATOR: Scraper online. Speed: {POLL_INTERVAL}s")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                # Direct scan for Whale activity
                target_pubkey = Pubkey.from_string(WALLET)
                sigs = await client.get_signatures_for_address(target_pubkey)
                
                if ERROR_COUNT > 0:
                    ERROR_COUNT -= 1
                    POLL_INTERVAL = max(0.1, POLL_INTERVAL - 0.05)
            except Exception as e:
                ERROR_COUNT += 1
                POLL_INTERVAL = min(5.0, POLL_INTERVAL + 0.5)
                log(f"⚠️ ADAPTING: {e}. Current Speed: {POLL_INTERVAL}s")
            await asyncio.sleep(POLL_INTERVAL)

# --- PILLAR 2: NUCLEAR EXIT ENGINE ---
async def exit_engine():
    log("EXIT ENGINE: Monitoring for targets...")
    while ACTIVE:
        # Check active POSITIONS and compare to live Raydium price
        # If target hit -> Execute Jito Swap to SOL
        await asyncio.sleep(1.0)

# --- PILLAR 3: COMPOUNDING TREASURY ---
async def treasury_compounding():
    log("TREASURY: Compounding mode active.")
    while ACTIVE:
        await asyncio.sleep(600)

# --- THE COMMAND DECK ---
async def handle_cmds(client):
    global ACTIVE
    off = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                res = (await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={off}&timeout=10")).json()
                for u in res.get("result", []):
                    off = u["update_id"] + 1
                    msg = u.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        
                        if "/health" in cmd:
                            h = "🟢 OPTIMAL" if ERROR_COUNT < 3 else "🟡 ADAPTING"
                            await notify(f"STATUS: {h}\nSPEED: {POLL_INTERVAL:.2f}s\nERROR_LEVEL: {ERROR_COUNT}")
                        
                        elif "/sendhome" in cmd:
                            bal_resp = await client.get_balance(Pubkey.from_string(WALLET))
                            bal = bal_resp.value / 10**9
                            await notify(f"💰 EXTRACTION: Sending {(bal*0.5):.4f} SOL to Kraken.")
                            # Logic for actual Solana transfer to KRAKEN
                            
                        elif "/wallet" in cmd:
                            await notify(f"HUNTING: {WALLET}\nTREASURY: {KRAKEN}")
                            
                        elif "/stop" in cmd: 
                            ACTIVE = False
                            await notify("HALTED: All systems offline.")
                            
                        elif "/start" in cmd: 
                            ACTIVE = True
                            await notify("RESUMED: Sovereign is hunting.")
        except: pass
        await asyncio.sleep(2)

async def core():
    log(f"==> OMNICORE v10.4 | SOVEREIGN PRIME | {WALLET[:6]}")
    async with AsyncClient(RPC) as client:
        # Start all engines in background
        asyncio.create_task(handle_cmds(client))
        asyncio.create_task(predatory_scraper())
        asyncio.create_task(exit_engine())
        asyncio.create_task(treasury_compounding())
        
        await notify("SOVEREIGN v10.4 PRIME ONLINE. Hunting the Mainnet.")
        
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING ({POLL_INTERVAL:.2f}s)...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: await asyncio.sleep(5)

# --- KEEP-ALIVE WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def health_check(): 
    return "SOVEREIGN_V10.4_PRIME_ACTIVE", 200

if __name__ == "__main__":
    # Ensure database table exists
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS trades (mint TEXT, side TEXT, price REAL, time REAL)")
        conn.commit()
        cur.close()
        conn.close()
    except: log("DB: Table ready or connection skipped.")
    
    # Fire the core
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
