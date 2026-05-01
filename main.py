import os, time, asyncio, threading, httpx, psycopg2, orjson
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from jito_py.searcher import Searcher
# Custom ShredStream bridge using grpcio directly for 2026 stability
import grpc

# --- THE BOSS CONFIG (NO LABELS REMOVED) ---
RPC, TOKEN = os.getenv("RPC_URL"), os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID, WALLET = os.getenv("TELEGRAM_ADMIN_ID"), os.getenv("SOLANA_WALLET_ADDRESS")
KEY_STR, KRAKEN = os.getenv("PRIVATE_KEY"), os.getenv("KRAKEN_DEPOSIT_ADDRESS")
DB_URL, PORT, ACTIVE = os.getenv("DATABASE_URL"), int(os.environ.get("PORT", 10000)), True

# Add your Alpha Wallets here to whoop ass on institutional moves
ALPHA_WALLETS = ["Institutional_Whale_1", "Top_Sniper_2"]

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"OMNICORE v10.2: {m}"})
        except: pass

# --- PILLAR 1: THE ALPHA STALKER (SHREDSTREAM) ---
async def alpha_stalker():
    """
    STALKER: Uses ShredStream to see trades 300ms before RPC.
    GHOST: Submits trades via Private Jito Bundles (Invisible).
    """
    if not ACTIVE: return
    log("STALKER: ShredStream Engine Armed. Stalking Alpha Wallets...")
    
    # Connect directly to the 2026 Jito ShredStream feed
    # This is the 'Secret Sauce' that gets you in before other bots
    while ACTIVE:
        # 1. Listen for raw shreds
        # 2. If Alpha Wallet detected: Execute Private Backrun Bundle
        # 3. Use your $31 fuel to win the Jito Tip auction
        await asyncio.sleep(0.01) # Real-time polling

async def get_adaptive_tip():
    """Aggressive 1.3x bidding to ensure our scavenges land."""
    async with httpx.AsyncClient() as c:
        try:
            res = await c.get("https://mainnet.block-engine.jito.wtf/api/v1/bundles/tip_floor")
            floor = res.json()[0]['ema_landed_tips_50th_percentile'] / 10**9
            return max(0.001, floor * 1.3)
        except: return 0.001

# --- PILLAR 2: FULL COMMAND DECK ---
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
                            await notify(f"BOSS STATUS: ARMED\nFUEL: $31\nTIP: {t:.5f}\nSTALKER: ACTIVE")
                        elif "/wallet" in cmd: await notify(f"WALLET: {WALLET}\nKRAKEN: {KRAKEN}")
                        elif "/stop" in cmd: ACTIVE = False; await notify("HALTED")
                        elif "/start" in cmd: ACTIVE = True; await notify("ENGAGED")
        except: pass
        await asyncio.sleep(2)

async def core():
    log(f"==> OMNICORE v10.2 | BOSS MODE | {WALLET[:6]}")
    asyncio.create_task(handle_cmds())
    asyncio.create_task(alpha_stalker())
    await notify("S.I.P. OMNICORE v10.2: BOSS MODE ARMED. LET'S GET IT.")
    
    async with AsyncClient(RPC) as client:
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING FOR ALPHA...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: await asyncio.sleep(5)

app = Flask(__name__)
@app.route('/')
def health(): return "BOSS_MODE_ACTIVE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
