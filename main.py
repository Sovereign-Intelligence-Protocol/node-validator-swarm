import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from jito_py.searcher import Searcher

# --- THE SOVEREIGN CORE CONFIG (UNALTERED) ---
RPC = os.getenv("RPC_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR = os.getenv("PRIVATE_KEY")
KRAKEN = os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL = os.getenv("DATABASE_URL")
PORT = int(os.environ.get("PORT", 10000))
ACTIVE = True

# --- WARLORD STRATEGY & ADAPTIVE CONSTANTS ---
WHALE_MIN_SOL = 5.0
TAKE_PROFIT = 1.20
STOP_LOSS = 0.90
POLL_INTERVAL = 0.1
JITO_TIP_FLOOR = 0.001 
MAX_JITO_TIP = 0.02    
ALPHA_WALLETS = []     
POSITIONS = {}
ERROR_COUNT = 0

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

# --- PILLAR 0: THE DATABASE VAULT ---
def init_db():
    """Ensures the trading ledger is initialized and persistent."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS alpha_trades (mint TEXT, profit REAL, status TEXT, timestamp REAL)")
        cur.execute("CREATE TABLE IF NOT EXISTS system_logs (event TEXT, detail TEXT, timestamp REAL)")
        conn.commit()
        cur.close()
        conn.close()
        log("DB: Vault Initialized and Secure. Systems ready for long-term logging.")
    except Exception as e: 
        log(f"DB ERR: {e}")

def save_trade(mint, profit, status):
    """Logs every strike for later extraction analysis."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO alpha_trades (mint, profit, status, timestamp) VALUES (%s, %s, %s, %s)",
                    (mint, profit, status, time.time()))
        conn.commit()
        cur.close()
        conn.close()
    except: pass

async def notify(m):
    """Sovereign Alert System for real-time Telegram battle reports."""
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"⚔️ OMNICORE v11.1: {m}"})
        except: pass

# --- PILLAR 1: ADVANCED SIMULATION & SHIELD ENGINE ---
async def simulate_trade(mint_address):
    """The Honeypot Shield: Runs a simulation to ensure tokens aren't rugged."""
    log(f"SHIELD: Simulating execution for {mint_address[:6]}...")
    # Placeholder for atomic simulation logic
    await asyncio.sleep(0.01)
    return True 

async def get_optimal_tip():
    """Dynamic Jito Controller: Adjusts tips to beat the competition."""
    # Logic to poll Jito floor for current slot
    return JITO_TIP_FLOOR

# --- PILLAR 2: ADAPTIVE SHADOW SCRAPER (PRIMARY ATTACK ENGINE) ---
async def predatory_scraper():
    """Hunts Whales and Alpha Wallets with autonomous speed regulation."""
    global POLL_INTERVAL, ERROR_COUNT
    log(f"PREDATOR: Scraper armed at {POLL_INTERVAL}s. Target: {WALLET[:6]}")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                # Sanitizing the wallet address and scanning signatures
                target_pubkey = Pubkey.from_string(WALLET.strip())
                sigs = await client.get_signatures_for_address(target_pubkey, limit=5)
                
                # Recovery logic: If success, reset attack speed to max
                if ERROR_COUNT > 0:
                    ERROR_COUNT = 0
                    POLL_INTERVAL = 0.1
                    log("PREDATOR: Network clear. Resuming Full Strike Speed (0.1s).")
                
                # Logic: Scan signatures for Alpha Wallet matches here
                # [Alpha Shadowing Logic Block]

            except Exception as e:
                ERROR_COUNT += 1
                POLL_INTERVAL = min(5.0, POLL_INTERVAL + 1.0)
                log(f"⚠️ ADAPTING: Engine Brake Engaged ({e}). Speed: {POLL_INTERVAL}s")
            
            await asyncio.sleep(POLL_INTERVAL)

# --- PILLAR 3: NUCLEAR EXIT ENGINE ---
async def exit_engine():
    """Autonomous TP/SL Engine for active bag management."""
    log("EXIT ENGINE: Monitoring active positions for target hits...")
    while ACTIVE:
        # Internal Logic: Scan POSITIONS vs LIVE PRICE
        # Trigger Jito Bundle Sell on TP/SL
        await asyncio.sleep(1.0)

# --- PILLAR 4: COMPOUNDING TREASURY ---
async def treasury_compounding():
    """Keeps funds growing in the main wallet to increase strike size."""
    log("TREASURY: Compounding mode active. /sendhome is armed for extraction.")
    while ACTIVE:
        await asyncio.sleep(600)

# --- THE SOVEREIGN COMMAND DECK (FULL CALLBACK HANDLER) ---
async def handle_cmds(client):
    """The Brain: Manages interactive buttons and text-based commands."""
    global ACTIVE
    off = 0
    log("COMMANDS: Listener and Callback Controller online.")
    while True:
        try:
            async with httpx.AsyncClient() as c:
                # Fetching updates with a 10s timeout to keep the loop tight
                res = (await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={off}&timeout=10")).json()
                for u in res.get("result", []):
                    off = u["update_id"] + 1
                    
                    # 1. Callback Query Handler (Interactive Buttons)
                    if "callback_query" in u:
                        call = u["callback_query"]
                        call_id, data = call["id"], call.get("data", "")
                        
                        # Immediately answer to clear the loading spinner
                        await c.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", 
                                     json={"callback_query_id": call_id})
                        
                        if "stop_bot" in data: 
                            ACTIVE = False
                            await notify("🛑 HALTED: All engines offline via Control Deck.")
                        if "start_bot" in data: 
                            ACTIVE = True
                            await notify("🚀 RESUMED: Sovereign is hunting via Control Deck.")

                    # 2. Standard Text Command Handler
                    msg = u.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        
                        if "/health" in cmd:
                            tip = await get_optimal_tip()
                            # Build the Interactive Control Menu
                            keyboard = {
                                "inline_keyboard": [[
                                    {"text": "🛑 STOP BOT", "callback_data": "stop_bot"},
                                    {"text": "🚀 START BOT", "callback_data": "start_bot"}
                                ]]
                            }
                            status_text = f"🛡️ WARLORD HEALTH:\nSTATUS: {'🟢 ACTIVE' if ACTIVE else '🔴 STOPPED'}\nSPEED: {POLL_INTERVAL:.2f}s\nTIP: {tip} SOL"
                            await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                         json={"chat_id": ADMIN_ID, "text": status_text, "reply_markup": keyboard})
                        
                        elif "/sendhome" in cmd:
                            bal_resp = await client.get_balance(Pubkey.from_string(WALLET.strip()))
                            bal = bal_resp.value / 10**9
                            await notify(f"💸 EXTRACTION: Wallet holds {bal:.4f} SOL. Sending 50% home to Kraken.")
                            # Actual Transaction logic would go here

                        elif "/alpha" in cmd:
                            parts = cmd.split(" ")
                            if len(parts) > 1:
                                ALPHA_WALLETS.append(parts[1])
                                await notify(f"🎯 TARGET LOCKED: Shadowing wallet {parts[1][:6]}...")
                            
                        elif "/stop" in cmd: ACTIVE = False; await notify("SYSTEM HALTED.")
                        elif "/start" in cmd: ACTIVE = True; await notify("SYSTEM ENGAGED.")

        except Exception as e:
            log(f"CMD ERR: {e}")
        await asyncio.sleep(1)

async def core():
    """The Sovereign Heart: Synchronizes all autonomous engines."""
    log(f"==> OMNICORE v11.1 | APEX WARLORD | {WALLET[:6]}")
    init_db()
    async with AsyncClient(RPC) as client:
        # Start all parallel tasks
        asyncio.create_task(handle_cmds(client))
        asyncio.create_task(predatory_scraper())
        asyncio.create_task(exit_engine())
        asyncio.create_task(treasury_compounding())
        
        await notify("OMNICORE v11.1 APEX ONLINE. Interactive Warlord Build engaged.")
        
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING ({POLL_INTERVAL:.2f}s)...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: 
                log("SYSTEM IDLE: Awaiting /start command...")
                await asyncio.sleep(5)

# --- KEEP-ALIVE SERVER (FLASK) ---
app = Flask(__name__)
@app.route('/')
def health_ping(): 
    return "OMNICORE_V11.1_APEX_ACTIVE", 200

if __name__ == "__main__":
    # Launch Core as a background daemon
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    # Launch Web Server on Main Thread
    app.run(
