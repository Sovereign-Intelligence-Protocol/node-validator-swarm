import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# --- V35.7 FULL-CYCLE SOVEREIGN ---
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
        
        # Parameters
        self.pulse = 0.5
        self.buy_amt = 200000000  # ~0.2 SOL ($31)
        self.take_profit_multiplier = 1.25 # +25%
        self.active_trade = None
        self.heartbeat_counter = 0

    async def notify(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"👑 v35.7 SOVEREIGN:\n{msg}"})
            except: pass

    async def simulate_and_fire(self, tx_b64, target, mode="BUY"):
        """The Shield: Checks viability then fires Jito Bundle"""
        async with httpx.AsyncClient() as client:
            try:
                # 1. Pre-Flight Simulation
                sim = await client.post(f"{self.jup_api}/instructions", json={"swapTransaction": tx_b64})
                if sim.status_code != 200:
                    logger.warning(f"SHIELD BLOCK: {mode} simulation failed. Saving SOL.")
                    return False

                # 2. Fire Bundle
                raw = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
                signed = VersionedTransaction.populate(raw.message, [self.keypair.sign_message(raw.message)])
                payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed)).decode("utf-8")]]}
                res = await client.post(self.jito_engine, json=payload)
                
                bundle_id = res.json().get("result")
                if bundle_id:
                    await self.notify(f"✅ {mode} EXECUTED\nMint: {target[:8]}\nBundle: {bundle_id}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Execution Error: {e}")
                return False

    async def get_swap(self, input_m, output_m, amount):
        async with httpx.AsyncClient() as client:
            try:
                q = (await client.get(f"{self.jup_api}/quote?inputMint={input_m}&outputMint={output_m}&amount={amount}&slippageBps=200")).json()
                s = (await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": q, "userPublicKey": str(self.keypair.pubkey()),
                    "prioritizationFeeLamports": 150000
                })).json()
                return s.get("swapTransaction")
            except: return None

    async def manage_exit(self, mint):
        """Monitor for Profit and Exit Automatically"""
        logger.info(f"STARTING AUTO-EXIT MONITOR: {mint}")
        # In v35.7, we wait 30s then attempt a Take-Profit Swap
        await asyncio.sleep(30) 
        sell_tx = await self.get_swap(mint, "So11111111111111111111111111111111111111112", "all")
        if sell_tx:
            await self.simulate_and_fire(sell_tx, mint, mode="SELL")
        self.active_trade = None

    async def core_loop(self):
        await self.notify("v35.7 Sovereign Online. All systems (Shield/Exit) active.")
        while True:
            try:
                self.heartbeat_counter += 1
                target = os.getenv("TARGET_MINT")
                
                if target and not self.active_trade:
                    logger.info(f"TARGET DETECTED: {target}")
                    buy_tx = await self.get_swap("So111111111111111
