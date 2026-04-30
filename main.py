import os, time, asyncio, threading, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient

# --- CONFIG ---
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
@app.route('/')
def health(): return "S.I.P. OMNICORE V6.1 LIVE", 200

async def telegram_log(msg):
    if TOKEN:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": "@me", "text": msg})

async def scan_logic():
    print("==> SYSTEM START: INITIALIZING SCANNER...")
    async with AsyncClient(RPC) as client:
        while True:
            try:
                # 2-SECOND TARGET SCAN
                res = await client.get_slot()
                print(f"[{time.strftime('%H:%M:%S')}] OMNICORE SCANNING SLOT: {res.value}")
                
                # YOUR MEV / JITO BUNDLE LOGIC HERE
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"CORE ERROR: {e}")
                await asyncio.sleep(5)

def background_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scan_logic())

if __name__ == "__main__":
    # START SCANNER IN BACKGROUND
    threading.Thread(target=background_worker, daemon=True).start()
    
    # START RENDER WEB SERVER
    print(f"==> BINDING TO PORT {PORT}")
    app.run(host='0.0.0.0', port=PORT)
