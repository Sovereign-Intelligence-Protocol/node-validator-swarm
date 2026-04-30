import os, time, asyncio, threading, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient

# 1. IMMEDIATE STARTUP LOG
print("==> SYSTEM BOOT: S.I.P. OMNICORE V6.2")

RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PORT = int(os.environ.get("PORT", 10000))

async def scan_logic():
    print(f"==> CONNECTING TO RPC: {RPC}")
    async with AsyncClient(RPC) as client:
        while True:
            try:
                res = await client.get_slot()
                print(f"!!! [SUCCESS] SLOT: {res.value} !!!")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"!!! [RPC ERROR]: {e} !!!")
                await asyncio.sleep(5)

def worker():
    asyncio.run(scan_logic())

# 2. START THE ENGINE BEFORE THE WEB SERVER
threading.Thread(target=worker, daemon=True).start()

app = Flask(__name__)
@app.route('/')
def health(): return "ACTIVE", 200

if __name__ == "__main__":
    print(f"==> STARTING WEB SERVER ON PORT {PORT}")
    app.run(host='0.0.0.0', port=PORT)
