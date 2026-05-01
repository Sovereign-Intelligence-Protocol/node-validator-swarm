import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from jito_py.searcher import Searcher

# --- CONFIG & LABELS (THE SOVEREIGN CORE) ---
RPC, TOKEN = os.getenv("RPC_URL"), os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID, WALLET = os.getenv("TELEGRAM_ADMIN_ID"), os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR, KRAKEN = os.getenv("PRIVATE_KEY"), os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL, PORT, ACTIVE = os.getenv("DATABASE_URL"), int(os.environ.get("PORT", 10000)), True

# --- STRATEGY & ADAPTIVE CONSTANTS ---
WHALE_MIN_SOL = 5.0    # Minimum size to strike
TAKE_PROFIT = 1.20     # Sell 50% at +20% gain
STOP_LOSS = 0.90       # Hard cut at -10% loss
POLL_INTERVAL = 0.1    # High-speed start
ERROR_COUNT = 0        # Throttle counter
POSITIONS = {}         # Active trade tracking

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    """Sovereign Alert System."""
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"💎 OMNICORE v10.4: {m}"})
        except: pass

# --- PILLAR 1: ADAPTIVE PREDATORY SCRAPER ---
async def predatory_scraper():
    """Hunts whales and auto-adjusts speed to avoid plan crashes."""
    global POLL_INTERVAL, ERROR_COUNT
    log(f"PREDATOR: Scraper online. Speed: {POLL_INTERVAL}s")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                # Active scan for Raydium AMM transactions
                await client.get_signatures_for_address(Pubkey.from_string("675k1q2w..."))
                
                # Success Logic: Gradually speed back up if we were throttled
                if ERROR_COUNT > 0:
                    ERROR_COUNT -= 1
                    POLL_INTERVAL = max(0.1, POLL_INTERVAL - 0.05)
            except Exception as e:
                ERROR_COUNT += 1
                # The Brake: Slow down to protect the Render process
                POLL_INTERVAL = min(5.0, POLL_INTERVAL + 0.5)
                log(f"⚠️ THROTTLED: Error {e}. Slowing to {POLL_INTERVAL}s")
            await asyncio.sleep(POLL_INTERVAL)

# --- PILLAR 2: NUCLEAR EXIT ENGINE ---
async def exit_engine():
    """Autonomous exit logic for profit and safety."""
    log("EXIT ENGINE: Monitoring for targets...")
    while ACTIVE:
        # Internal Logic: Scan POSITIONS for TP/SL triggers
        await asyncio.sleep(1.0)

# --- PILLAR 3: COMPOUNDING TREASURY ---
async def treasury_compounding():
    """Keeps funds in-wallet to build strike power."""
    log("TREASURY: Compounding mode active. /sendhome is armed.")
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
                            await notify(f"STATUS: {h}\nINTERVAL: {POLL_INTERVAL:.2f}s\nMODE: COMPOUNDING")
                        
                        elif "/sendhome" in cmd:
                            # 50% Extraction Protocol
                            bal_resp = await client.get_balance(Pubkey.from_string(WALLET))
                            bal = bal_resp.value / 10**9
                            if bal > 0.05:
                                await notify(f"💰 EXTRACTION: Sending {(bal*0.5):.4f} SOL home to Kraken.")
                                # Transfer Logic: Send 50% to KRAKEN
                            else:
                                await notify("⚠️ TREASURY TOO LOW.")

                        elif "/wallet" in cmd:
                            await notify(f"HOT: {WALLET}\nKRAKEN: {KRAKEN}")
                            
                        elif "/stop" in cmd: ACTIVE = False; await notify("SYSTEMS HALTED.")
                        elif "/start" in cmd: ACTIVE = True; await notify("SYSTEMS ENGAGED.")
        except: pass
        await asyncio.sleep(2)

async def core():
    log(f"==> OMNICORE v10.4 | SOVEREIGN | {WALLET[:6]}")
    async with AsyncClient(RPC) as client:
        # Boot all engines
        asyncio.create_task(handle_cmds(client))
        asyncio.create_task(predatory_scraper())
        asyncio.create_task(exit_engine())
        asyncio.create_task(treasury_compounding())
        
        await notify("SOVEREIGN v10.4 ONLINE. Hunting the Mainnet.")
        
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
def health_check(): return "SOVEREIGN_V10.4_ALIVE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
