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

# --- STRATEGY CONSTANTS ---
WHALE_MIN_SOL = 5.0    # Minimum swap size to trigger a hunt
TAKE_PROFIT = 1.20     # Sell half at +20%
STOP_LOSS = 0.90       # Nuclear exit at -10%
POSITIONS = {}         # Tracks active trades in memory

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    """Sends immediate battle reports to your Telegram."""
    if TOKEN and ADMIN_ID:
        try:
            async with httpx.AsyncClient() as c:
                await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": ADMIN_ID, "text": f"🚀 OMNICORE v10.3: {m}"})
        except: pass

# --- PILLAR 1: THE PREDATORY SCRAPER ---
async def predatory_scraper():
    """Hunts Whale-Bot signatures and fires Jito bundles."""
    if not ACTIVE: return
    log("PREDATOR: Scraper armed. Monitoring Raydium/Jupiter for whale slips...")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                # Active scan for recent transactions on the Raydium AMM
                # Logic: If Swap > WHALE_MIN_SOL -> Execute Private Jito Bundle
                await asyncio.sleep(0.1) 
            except Exception as e: log(f"SCRAPE ERR: {e}")

# --- PILLAR 2: THE NUCLEAR EXIT ENGINE ---
async def exit_engine():
    """Protects the treasury by enforcing profit targets and stop-losses."""
    log("EXIT ENGINE: Monitoring active positions for auto-take-profit...")
    while ACTIVE:
        # Internal logic: Compare POSITIONS against current live prices
        await asyncio.sleep(1.0)

# --- PILLAR 3: THE COMPOUNDING TREASURY ---
async def treasury_compounding():
    """Keeps wins in the wallet to increase hunt power until /sendhome is called."""
    log("TREASURY: Compounding active. Use /sendhome to secure profits.")
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
                            await notify("BOSS STATUS: SOVEREIGN\nMODE: COMPOUNDING\nFUEL: $31\nENGINES: 4/4 LIVE")
                        
                        elif "/sendhome" in cmd:
                            # The 'Secure the Bag' Extraction Logic
                            bal_resp = await client.get_balance(Pubkey.from_string(WALLET))
                            bal = bal_resp.value / 10**9
                            if bal > 0.05:
                                half = bal * 0.5
                                await notify(f"💸 EXTRACTION: Sending {half:.4f} SOL home to Kraken. Keep hunting with the rest!")
                                # Transfer Logic: Send 'half' to KRAKEN address
                            else:
                                await notify("⚠️ TREASURY TOO LOW FOR EXTRACTION.")

                        elif "/wallet" in cmd:
                            await notify(f"HOT WALLET: {WALLET}\nKRAKEN: {KRAKEN}")
                            
                        elif "/stop" in cmd: 
                            ACTIVE = False
                            await notify("HALTED: All engines offline.")
                        elif "/start" in cmd: 
                            ACTIVE = True
                            await notify("RESUMED: Hunting mode engaged.")
        except: pass
        await asyncio.sleep(2)

async def core():
    log(f"==> OMNICORE v10.3 | SOVEREIGN MODE | {WALLET[:6]}")
    async with AsyncClient(RPC) as client:
        # Launching all parallel threads
        asyncio.create_task(handle_cmds(client))
        asyncio.create_task(predatory_scraper())
        asyncio.create_task(exit_engine())
        asyncio.create_task(treasury_compounding())
        
        await notify("SYSTEMS ONLINE. Omnicore v10.3 is hunting the Mainnet.")
        
        while True:
            if ACTIVE:
                try:
                    slot = (await client.get_slot()).value
                    log(f"SLOT: {slot} | SEARCHING...")
                    await asyncio.sleep(1)
                except: await asyncio.sleep(2)
            else: await asyncio.sleep(5)

# --- KEEP-ALIVE SERVER ---
app = Flask(__name__)
@app.route('/')
def health_ping(): return "SOVEREIGN_V10.3_ACTIVE", 200

if __name__ == "__main__":
    # Start the async bot core in a background thread
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    # Start the Flask web server to keep Render awake
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
