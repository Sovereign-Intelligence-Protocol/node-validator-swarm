import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# --- V35.7 REPAIR: FULL-CYCLE SOVEREIGN ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOVEREIGN-v35.7 - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health():
    return {"status": "FULL-CYCLE", "engine": "v35.7", "state": "AUTONOMOUS"}, 200

class FullCycleSovereign:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.pulse = 0.5
        self.buy_amt = 200000000 
        self.active_trade = None
        self.heartbeat_counter = 0

    async def notify(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"👑 v35.7 SOVEREIGN:\n{msg}"})
            except: pass

    async def simulate_and_fire(self, tx_b64, target, mode="BUY"):
        async with httpx.AsyncClient() as client:
            try:
                sim = await client.post(f"{self.jup_api}/instructions", json={"swapTransaction": tx_b64})
                if sim.status_code != 200: return False
                raw = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
                signed = VersionedTransaction.populate(raw.message, [self.keypair.sign_message(raw.message)])
                payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed)).decode("utf-8")]]}
                res = await client.post(self.jito_engine, json=payload)
                bundle_id = res.json().get("result")
                if bundle_id:
                    await self.notify(f"✅ {mode} EXECUTED\nMint: {target[:8]}\nBundle: {bundle_id}")
                    return True
                return False
            except: return False

    async def get_swap(self, input_m, output_m, amount):
        async with httpx.AsyncClient() as client:
            try:
                q_url = f"{self.jup_api}/quote?inputMint={input_m}&outputMint={output_m}&amount={amount}&slippageBps=200"
                q = (await client.get(q_url)).json()
                s = (await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": q, "userPublicKey": str(self.keypair.pubkey()),
                    "prioritizationFeeLamports": 150000
                })).json()
                return s.get("swapTransaction")
            except: return None

    async def manage_exit(self, mint):
        await asyncio.sleep(30) 
        sell_tx = await self.get_swap(mint, "So11111111111111111111111111111111111111112", "all")
        if sell_tx:
            await self.simulate_and_fire(sell_tx, mint, mode="SELL")
        self.active_trade = None

    async def core_loop(self):
        await self.notify("v35.7 Fixed. All systems (Shield/Exit) active.")
        while True:
            try:
                self.heartbeat_counter += 1
                target = os.getenv("TARGET_MINT")
                if target and not self.active_trade:
                    buy_tx = await self.get_swap("So11111111111111111111111111111111111111112", target, self.buy_amt)
                    if buy_tx:
                        if await self.simulate_and_fire(buy_tx, target, mode="BUY"):
                            self.active_trade = target
                            asyncio.create_task(self.manage_exit(target))
                if self.heartbeat_counter % 20 == 0:
                    logger.info(f"ALIVE: Scan {self.heartbeat_counter}")
                await asyncio.sleep(self.pulse)
            except: await asyncio.sleep(2)

def run_server():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    engine = FullCycleSovereign()
    asyncio.run(engine.core_loop())
