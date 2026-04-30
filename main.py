import os, time, asyncio, threading, httpx
from flask import Flask
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

# --- ENVIRONMENT SETUP ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KEY = os.getenv("PRIVATE_KEY")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE_V6_LIVE", 200

async def telegram_alert(msg):
    if TOKEN:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": "@me", "text": msg})

async def main_loop():
    print("==> S.I.P. OMNICORE: System Initialized")
    async with AsyncClient(RPC) as client:
        while True:
            try:
                # 2-SECOND SCAN LOGIC
                res = await client.get_slot()
                slot = res.value
                print(f"[{time.strftime('%H:%M:%S')}] SCANNING SLOT: {slot}")
                
                # INTEGRATE JUPITER / JITO BUNDLE LOGIC HERE
                # if target_found: await telegram_alert(f"Trade Executed: {slot}")

                await asyncio.sleep(2)
            except Exception as e:
                print(f"CORE ERROR: {e}")
                await asyncio.sleep(5)

def run_back():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_loop())

if __name__ == "__main__":
    # Launch logic in background thread to prevent Render blocking
    threading.Thread(target=run_back, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
