import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# --- V35.6 THE SIGNAL (FIXED BOOT SEQUENCE) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - SIGNAL-v35.6 - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health():
    return {"status": "ACTIVE", "engine": "v35.6"}, 200

class SovereignSignal:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.pulse = 0.5 
        self.heartbeat_counter = 0

    async def notify(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"📡 v35.6 SIGNAL:\n{msg}"})
            except: pass

    async def execute_trade(self, target):
        async with httpx.AsyncClient() as client:
            try:
                q = (await client.get(f"{self.jup_api}/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={target}&amount=200000000&slippageBps=150")).json()
                s = (await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": q, "userPublicKey": str(self.keypair.pubkey()),
                    "prioritizationFeeLamports": 150000
                })).json()
                tx_b64 = s.get("swapTransaction")
                if not tx_b64: return
                raw = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
                signed = VersionedTransaction.populate(raw.message, [self.keypair.sign_message(raw.message)])
                payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed)).decode("utf-8")]]}
                await client.post(self.jito_engine, json=payload)
                await self.notify(f"🚀 TRADE EXECUTED\nTarget: {target[:8]}")
            except Exception as e: logger.error(f"Trade Error: {e}")

    async def core_loop(self):
        await self.notify("Engine v35.6 Online. Boot Sequence Complete.")
        while True:
            try:
                self.heartbeat_counter += 1
                target = os.getenv("TARGET_MINT")
                if target:
                    await self.execute_trade(target)
                
                if self.heartbeat_counter % 20 == 0:
                    logger.info(f"ALIVE: Scan {self.heartbeat_counter}")
                
                await asyncio.sleep(self.pulse)
            except Exception as e:
                await asyncio.sleep(2)

def run_server():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # 1. Start Flask in a separate thread so it doesn't block the engine
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 2. Run the actual Trading Engine
    engine = SovereignSignal()
    asyncio.run(engine.core_loop())
