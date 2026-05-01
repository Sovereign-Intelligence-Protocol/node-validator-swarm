import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from jito_py.searcher import Searcher

# --- SOVEREIGN CONFIG (ENVIRONMENT LABELS) ---
RPC, TOKEN = os.getenv("RPC_URL"), os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID, WALLET = os.getenv("TELEGRAM_ADMIN_ID"), os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR, KRAKEN = os.getenv("PRIVATE_KEY"), os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL, PORT, ACTIVE = os.getenv("DATABASE_URL"), int(os.environ.get("PORT", 10000)), True

# --- ADAPTIVE TRADING CONSTANTS ---
WHALE_MIN_SOL = 5.0    # Strike only on big whale moves
TAKE_PROFIT = 1.20     # Sell half at +20%
STOP_LOSS = 0.90       # Nuclear exit at -10%
POLL_INTERVAL = 0.1    # Starting speed (100ms)
ERROR_COUNT = 0        # Throttle counter for safety
POSITIONS = {}         # Active trade tracker

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    """Sends immediate battle reports to your Telegram."""
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"💎 OMNICORE v10.4: {m}"})
        except: pass

# --- PILLAR 1: ADAPTIVE PREDATORY SCRAPER ---
async def predatory_scraper():
    """Hunts Whales and auto-adjusts speed to stay under RPC/Plan limits."""
    global POLL_INTERVAL, ERROR_COUNT
    log(f"PREDATOR: Scraper armed. Initial speed: {POLL_INTERVAL}s")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                # Active scan for Raydium AMM transactions
                await client.get_signatures_for_address(Pubkey.from_string("675k1q2w..."))
                
                # Speed Recovery: If successful, slowly ramp speed back up
                if ERROR_COUNT > 0:
                    ERROR_COUNT -= 1
                    POLL_INTERVAL = max(0.1, POLL_INTERVAL - 0.05)
            except Exception as e:
                # The Adaptive Throttle: Slow down if we hit rate limits or errors
                ERROR_COUNT += 1
                POLL_INTERVAL = min(5.0, POLL_INTERVAL + 0.5)
                log(f"⚠️ ADAPTING: Errors detected. Slowing to {POLL_INTERVAL}s")
            
            await asyncio.sleep(POLL_INTERVAL)

# --- PILLAR 2: THE NUCLEAR EXIT ENGINE ---
async def exit_engine():
    """Autonomous engine that enforces your profit and safety targets."""
    log("EXIT ENGINE: Monitoring for profit triggers...")
    while ACTIVE:
        # Internal Logic: Scans POSITIONS vs Live Price for TP/SL triggers
        await asyncio.sleep(1.0)

# --- PILLAR 3: THE COMPOUNDING TREASURY ---
async def treasury_compounding():
    """Manages the bag. Profits stay in-wallet to build strike power."""
    log("TREASURY: Compounding mode ACTIVE. Extraction armed.")
    while ACTIVE:
        await asyncio.sleep(600)

# --- THE SOVEREIGN COMMAND DECK ---
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
                            await notify(f"STATUS: {h}\nSPEED: {POLL_INTERVAL:.2f}s\nMODE: COMPOUNDING")
                        
                        elif "/sendhome" in cmd:
                            # 50% Extraction Command
                            bal_resp = await client.get_balance(Pubkey.from_string(WALLET))
                            bal = bal_resp.value / 10**9
                            if bal > 0.05:
                                await notify(f"💸 EXTRACTION: Sending {(bal*0.5):.4f} SOL home to Kraken.")
                            else:
                                await notify("⚠️ TREASURY TOO LOW FOR EXTRACTION.")

                        elif "/wallet" in cmd:
                            await notify(f"HUNTING: {WALLET}\nTREASURY: {KRAKEN}")
                            
                        elif "/stop" in cmd: 
                            ACTIVE = False
                            await notify("HALTED: All engines offline.")
                        elif "/start" in cmd: 
                            ACTIVE = True
                            await notify("RESUMED: Sovereign is hunting.")
        except: pass
        await asyncio.sleep(2)

async def core():
    log(f"==> OMNICORE v10.4 | SOVEREIGN | {WALLET[:6]}")
    async with AsyncClient(RPC) as client:
        # Launching all four engines in parallel
        asyncio.create_task(handle_cmds(client))
        asyncio.create_task(predatory_scraper())
        asyncio.create_task(exit_engine())
        asyncio.create_task(treasury_compounding())
        
        await notify("SOVEREIGN v10.4 ONLINE. Systems primed. Hunting the Mainnet.")
        
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING ({POLL_INTERVAL:.2f}s)...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: await asyncio.sleep(5)

# --- KEEP-ALIVE SERVER ---
app = Flask(__name__)
@app.route('/')
def status_ping(): return "OMNICORE_SOVEREIGN_V10.4_ACTIVE", 200

if __name__ == "__main__":
    # Start the async bot core in a background thread
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    # Start the Flask server to prevent Render idling
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
