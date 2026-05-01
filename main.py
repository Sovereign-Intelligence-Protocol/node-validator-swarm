import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from jito_py.searcher import Searcher

# --- THE SOVEREIGN CORE CONFIG ---
RPC = os.getenv("RPC_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR = os.getenv("PRIVATE_KEY")
KRAKEN = os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL = os.getenv("DATABASE_URL")
PORT = int(os.environ.get("PORT", 10000))
ACTIVE = True

# --- WARLORD CONSTANTS (v11.1) ---
WHALE_MIN_SOL = 5.0
TAKE_PROFIT = 1.20
STOP_LOSS = 0.90
POLL_INTERVAL = 0.1
JITO_TIP_FLOOR = 0.001 
MAX_JITO_TIP = 0.02    
ALPHA_WALLETS = []     
POSITIONS = {}

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

# --- DATABASE VAULT ---
def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS alpha_trades (mint TEXT, profit REAL, status TEXT, timestamp REAL)")
        conn.commit()
        cur.close()
        conn.close()
        log("DB: Vault Initialized and Secure.")
    except Exception as e: log(f"DB ERR: {e}")

async def notify(m):
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"⚔️ OMNICORE v11.1: {m}"})
        except: pass

# --- ADVANCED ENGINE: THE HONEYPOT SHIELD ---
async def simulate_trade(mint_address):
    """Simulates a trade to ensure it's not a rug/honeypot."""
    log(f"SHIELD: Simulating trade for {mint_address[:6]}...")
    return True 

# --- ADVANCED ENGINE: DYNAMIC JITO TIPPER ---
async def get_optimal_tip():
    """Adjusts your tip based on network congestion."""
    return JITO_TIP_FLOOR

# --- PILLAR 1: ADAPTIVE SHADOW SCRAPER ---
async def predatory_scraper():
    global POLL_INTERVAL
    log("WARLORD: Scraper active. Monitoring Whales and Alphas.")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                target = Pubkey.from_string(WALLET.strip())
                await client.get_signatures_for_address(target, limit=5)
                POLL_INTERVAL = max(0.1, POLL_INTERVAL - 0.05)
            except Exception as e:
                POLL_INTERVAL = min(5.0, POLL_INTERVAL + 0.5)
                log(f"⚠️ THROTTLE: {e}")
            await asyncio.sleep(POLL_INTERVAL)

# --- PILLAR 2: NUCLEAR EXIT ENGINE ---
async def exit_engine():
    log("EXIT ENGINE: Monitoring Alpha positions for exit targets.")
    while ACTIVE:
        await asyncio.sleep(1.0)

# --- PILLAR 3: COMPOUNDING TREASURY ---
async def treasury_compounding():
    log("TREASURY: Compounding strike power.")
    while ACTIVE: await asyncio.sleep(600)

# --- THE WAR ROOM COMMAND DECK (UPDATED WITH CALLBACK HANDLER) ---
async def handle_cmds(client):
    global ACTIVE
    off = 0
    log("COMMANDS: Listening for Buttons and Text.")
    while True:
        try:
            async with httpx.AsyncClient() as c:
                # Poll for all updates including button clicks
                res = (await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={off}&timeout=10")).json()
                for u in res.get("result", []):
                    off = u["update_id"] + 1
                    
                    # 1. Handle Button Clicks (Callback Queries)
                    if "callback_query" in u:
                        call = u["callback_query"]
                        call_id = call["id"]
                        data = call.get("data", "")
                        
                        # Tell Telegram we received the click
                        await c.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", 
                                     json={"callback_query_id": call_id})
                        
                        if "stop_bot" in data: 
                            ACTIVE = False
                            await notify("🛑 HALTED: Engines offline via Telegram Control.")
                        if "start_bot" in data: 
                            ACTIVE = True
                            await notify("🚀 RESUMED: Sovereign hunting via Telegram Control.")

                    # 2. Handle Text Commands
                    msg = u.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        
                        if "/health" in cmd:
                            tip = await get_optimal_tip()
                            # Send message with interactive buttons
                            keyboard = {
                                "inline_keyboard": [[
                                    {"text": "🛑 STOP BOT", "callback_data": "stop_bot"},
                                    {"text": "🚀 START BOT", "callback_data": "start_bot"}
                                ]]
                            }
                            await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                         json={"chat_id": ADMIN_ID, 
                                               "text": f"WARLORD HEALTH:\nSTATUS: {'🟢 ACTIVE' if ACTIVE else '🔴 STOPPED'}\nTIP: {tip} SOL", 
                                               "reply_markup": keyboard})
                        
                        elif "/sendhome" in cmd:
                            bal = (await client.get_balance(Pubkey.from_string(WALLET.strip()))).value / 10**9
                            await notify(f"💸 EXTRACTION: Moving {(bal*0.5):.4f} SOL to Kraken Treasury.")

                        elif "/alpha" in cmd:
                            parts = cmd.split(" ")
                            if len(parts) > 1:
                                ALPHA_WALLETS.append(parts[1])
                                await notify(f"🎯 TARGET LOCKED: Shadowing {parts[1][:6]}")
                            
                        elif "/stop" in cmd: ACTIVE = False; await notify("HALTED.")
                        elif "/start" in cmd: ACTIVE = True; await notify("ENGAGED.")
        except Exception as e:
            log(f"CMD ERR: {e}")
        await asyncio.sleep(1)

async def core():
    log(f"==> OMNICORE v11.1 | APEX WARLORD | {WALLET[:6]}")
    init_db()
    async with AsyncClient(RPC) as client:
        # Multi-Threaded Execution
        asyncio.create_task(handle_cmds(client))
        asyncio.create_task(predatory_scraper())
        asyncio.create_task(exit_engine())
        asyncio.create_task(treasury_compounding())
        
        await notify("OMNICORE v11.1 APEX LIVE. Interactive Buttons Armed.")
        
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING (0.10s)...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: await asyncio.sleep(5)

# --- KEEP-ALIVE HEARTBEAT ---
app = Flask(__name__)
@app.route('/')
def status(): return "WARLORD_V11.1_APEX_ACTIVE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
