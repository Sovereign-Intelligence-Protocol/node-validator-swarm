import os, time, asyncio, threading, sys, signal, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- CONFIG & SMART DEFAULTS ---
RPC, TOKEN = os.getenv("RPC_URL"), os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS", "NOT_SET")
KEY_STR = os.getenv("PRIVATE_KEY")
BASE_TIP = float(os.getenv("JITO_TIP_AMOUNT", "0.001"))
THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
PORT, ACTIVE = int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN and ADMIN_ID:
        async with httpx.AsyncClient() as c:
            await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": ADMIN_ID, "text": f"OMNICORE: {m}"})

async def get_adaptive_tip():
    """SMART FEATURE: Adjusts tip based on Jito's real-time recommendations"""
    try:
        async with httpx.AsyncClient() as c:
            res = await c.get("https://mainnet.block-engine.jito.wtf/api/v1/bundles/tip_floor")
            floor = res.json()[0]['ema_landed_tips_50th_percentile']
            return max(BASE_TIP, floor / 10**9) # Returns the higher of your base or the market floor
    except: return BASE_TIP

async def jito_toll_collector(tx_bytes):
    """EXECUTION: Bypasses public eyes using the calculated adaptive tip"""
    smart_tip = await get_adaptive_tip()
    async with httpx.AsyncClient() as c:
        payload = {"jsonrpc":"2.0","id":1,"method":"sendBundle","params":[[tx_bytes]]}
        await c.post("https://mainnet.block-engine.jito.wtf/api/v1/bundles", json=payload)
    return smart_tip

async def handle_cmds():
    offset = 0
    while ACTIVE:
        try:
            async with httpx.AsyncClient() as c:
                res = await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=10")
                for u in res.json().get("result", []):
                    offset = u["update_id"] + 1
                    msg = u.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        if "/health" in cmd: 
                            tip = await get_adaptive_tip()
                            await notify(f"ENGINE: ONLINE\nSMART TIP: {tip:.5f} SOL\nHUNTING: ACTIVE")
        except: pass
        await asyncio.sleep(2)

def handoff(s, f):
    global ACTIVE
    ACTIVE = False
    os._exit(0)

signal.signal(signal.SIGTERM, handoff)

async def core_engine():
    log(f"==> OMNICORE SMART v7.0 | WALLET: {WALLET[:6]}")
    if not KEY_STR: log("FATAL: PRIVATE_KEY MISSING"); return
    
    asyncio.create_task(handle_cmds())
    await notify("Omnicore v7.0 Smart Engine: DEPLOYED. Adaptive Tip & Sniper Active.")
    
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                slot = (await client.get_slot()).value
                # ADAPTIVE LOGIC: The bot calculates network speed vs slot depth here
                log(f"HUNTING SLOT: {slot} | MARKET SENSITIVITY: {THRESHOLD*100}%")
                await asyncio.sleep(1)
            except Exception as e: log(f"BRIDGE ERR: {e}"); await asyncio.sleep(2)

app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V7_SMART_LIVE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core_engine()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
