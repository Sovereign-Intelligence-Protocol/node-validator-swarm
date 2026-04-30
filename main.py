import os, time, asyncio, threading, sys, signal, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- CONFIG ---
RPC = os.getenv("RPC_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
KEY = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
WALLET = os.getenv("SOLANA_WALLET_ADDRESS", "N/A")
PORT, ACTIVE = int(os.environ.get("PORT", 10000)), True

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

async def notify(m):
    if TOKEN and ADMIN_ID:
        async with httpx.AsyncClient() as c:
            await c.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                         json={"chat_id": ADMIN_ID, "text": f"OMNICORE: {m}"})

async def handle_commands():
    offset = 0
    while ACTIVE:
        try:
            async with httpx.AsyncClient() as c:
                res = await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30")
                data = res.json()
                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    msg = upd.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        cmd = msg.get("text", "").lower()
                        if cmd == "/health": await notify(f"Active on Slot. Health: OK")
                        elif cmd == "/hunt": await notify("Re-initializing Scan Loop...")
                        elif cmd == "/revenue": await notify("Revenue Report: [Logic Pending]")
        except Exception as e: log(f"CMD ERROR: {e}")
        await asyncio.sleep(5)

def handoff(s, f):
    global ACTIVE
    log("!!! SIGTERM: 120S MANUAL LAPSE !!!")
    ACTIVE = False
    time.sleep(120)
    os._exit(0)

signal.signal(signal.SIGTERM, handoff)

async def core_engine():
    log(f"==> OMNICORE V35.7 LIVE | WALLET: {WALLET[:6]}")
    asyncio.create_task(handle_commands()) # Starts listening for your commands
    async with AsyncClient(RPC) as client:
        while ACTIVE:
            try:
                res = await client.get_slot()
                log(f"SCANNING SLOT: {res.value}")
                await asyncio.sleep(2) 
            except Exception as e: log(f"CORE ERROR: {e}"); await asyncio.sleep(5)

app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V35.7_STABLE", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(core_engine()), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
