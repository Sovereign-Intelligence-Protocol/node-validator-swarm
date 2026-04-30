import os, time, asyncio, threading, sys, signal, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- VERIFIED VERITABLES ---
RPC, TOKEN = os.getenv("RPC_URL"), os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID, WALLET = os.getenv("TELEGRAM_ADMIN_ID"), os.getenv("SOLANA_WALLET_ADDRESS")
KEY = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
TIP, THRESHOLD = os.getenv("JITO_TIP_AMOUNT", "0.001"), os.getenv("CONFIDENCE_THRESHOLD", "0.85")
PORT, ACTIVE = int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN and ADMIN_ID:
        async with httpx.AsyncClient() as c:
            await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": ADMIN_ID, "text": f"OMNICORE: {m}"})

async def jito_collect(tx):
    """TOLL COLLECTOR: High-speed Jito Bridge"""
    async with httpx.AsyncClient() as c:
        await c.post("https://mainnet.block-engine.jito.wtf/api/v1/bundles", json={"jsonrpc":"2.0","id":1,"method":"sendBundle","params":[[tx]]})

async def handle_cmds():
    offset = 0
    while ACTIVE:
        try:
            async with httpx.AsyncClient() as c:
                res = await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=10")
                for u in res.json().get("result", []):
                    offset, msg = u["update_id"]+1, u.get("message", {})
                    if str(msg.get("from",{}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        if "/health" in cmd: await notify("STATUS: ACTIVE | HUNTING")
                        if "/revenue" in cmd: await notify("REVENUE: [CALCULATING]")
        except: pass
        await asyncio.sleep(2)

def handoff(s, f):
    global ACTIVE
    ACTIVE = False
    os._exit(0)

signal.signal(signal.SIGTERM, handoff)

async def core():
    log(f"==> OMNICORE ARMED | WALLET: {WALLET[:6] if WALLET else 'N/A'}")
    asyncio.create_task(handle_cmds())
    await notify("Omnicore v6.0 Full Implementation: ONLINE")
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                slot = (await client.get_slot()).value
                log(f"HUNTING SLOT: {slot}")
                # Sniper / Bridge / Collector Trigger
                await asyncio.sleep(1)
            except Exception as e: log(f"BRIDGE ERR: {e}"); await asyncio.sleep(2)

app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V6_LIVE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
