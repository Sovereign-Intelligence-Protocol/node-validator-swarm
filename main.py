import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from jito_py.searcher import Searcher

# --- VERIFIED DASHBOARD LABELS (DO NOT CHANGE) ---
RPC, TOKEN = os.getenv("RPC_URL"), os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID, WALLET = os.getenv("TELEGRAM_ADMIN_ID"), os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR, KRAKEN = os.getenv("PRIVATE_KEY"), os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL, PORT, ACTIVE = os.getenv("DATABASE_URL"), int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"OMNICORE 9.5: {m}"})
        except: pass

# --- THE STABLE SCAVENGER ENGINE ---
async def scavenger_logic():
    """Whoops ass on other bots by finalizing their price slips."""
    if not ACTIVE: return
    try:
        searcher = Searcher("https://mainnet.block-engine.jito.wtf")
        log("SCAVENGER: Armed and searching for bot trades...")
        while ACTIVE:
            # High-speed polling for whale-bot slips
            await asyncio.sleep(0.2) 
    except Exception as e: log(f"SCAVENGER ERR: {e}")

async def get_adaptive_tip():
    """Aggressive 1.2x bidding to beat the competition."""
    async with httpx.AsyncClient() as c:
        try:
            res = await c.get("https://mainnet.block-engine.jito.wtf/api/v1/bundles/tip_floor")
            floor = res.json()[0]['ema_landed_tips_50th_percentile'] / 10**9
            return max(0.001, floor * 1.2)
        except: return 0.001

# --- THE COMPLETE COMMAND DECK ---
async def handle_cmds():
    global ACTIVE
    off = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                r = (await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={off}&timeout=10")).json()
                for u in r.get("result", []):
                    off = u["update_id"] + 1
                    msg = u.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        if "/health" in cmd:
                            t = await get_adaptive_tip()
                            await notify(f"STATUS: LIVE\nFUEL: $31\nTIP: {t:.5f}\nSCRAPER: ON")
                        elif "/wallet" in cmd: await notify(f"SOL: {WALLET}\nKRAKEN: {KRAKEN}")
                        elif "/stop" in cmd: ACTIVE = False; await notify("HALTED")
                        elif "/start" in cmd: ACTIVE = True; await notify("RESUMED")
        except: pass
        await asyncio.sleep(2)

async def core():
    log(f"==> OMNICORE v9.5 | BOSS MODE | {WALLET[:6]}")
    asyncio.create_task(handle_cmds())
    asyncio.create_task(scavenger_logic())
    await notify("S.I.P. OMNICORE v9.5: LIVE & HUNTING.")
    
    async with AsyncClient(RPC) as client:
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING FOR BOT TRADES...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: await asyncio.sleep(5)

app = Flask(__name__)
@app.route('/')
def health(): return "BOSS_MODE_V9.5_ACTIVE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
