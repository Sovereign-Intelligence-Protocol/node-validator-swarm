import os, asyncio, json, websockets, httpx
from solders.keypair import Keypair

# PRODUCTION CONFIG
RPC_URL = os.getenv("RPC_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_SIGNER = os.getenv("JITO_SIGNER_PRIVATE_KEY")
PORT = int(os.getenv("PORT", "10000"))

async def v38_engine():
    retries = 0
    while True:
        try:
            async with websockets.connect(RPC_URL) as ws:
                print(f"v38.0 IRON VAULT LIVE")
                retries = 0
                sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["6EF8rrecth7D..."]}, {"commitment":"processed"}]}
                await ws.send(json.dumps(sub))
                async for msg in ws:
                    # Trading logic here
                    pass
        except Exception as e:
            wait = min(2 ** retries, 30)
            print(f"v38 Connection Retry ({e}). Waiting {wait}s...")
            await asyncio.sleep(wait)
            retries += 1

async def main():
    # 1. Start the Port 10000 server FIRST to kill the 502 error
    server = await asyncio.start_server(lambda r, w: None, '0.0.0.0', PORT)
    print(f"v38.0 Heartbeat Online on Port {PORT}")
    
    # 2. Keep the server alive while running the engine
    async with server:
        await v38_engine()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
