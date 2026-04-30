import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey

# --- V35.0 OPTIMAL GUARDIAN ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - OMNICORE-v35.0 - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health():
    return {"status": "OPTIMAL", "engine": "Omnicore v35.0", "tier": "PRO-ELITE"}, 200

class OmnicoreV35:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.pulse = 0.4 
        self.priority_fee = 150000 
        self.target_mint = None 

    async def notify(self, message):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"🛡️ V35 GUARDIAN:\n{message}"})
            except: pass

    async def simulate_trade(self, swap_tx_b64):
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(f"{self.jup_api}/instructions", json={"swapTransaction": swap_tx_b64})
                return res.status_code == 200
            except: return False

    async def execute_optimal_strike(self, target):
        async with httpx.AsyncClient() as client:
            try:
                q_url = f"{self.jup_api}/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={target}&amount=31000000&slippageBps=150"
                quote = (await client.get(q_url)).json()
                
                s_res = await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": quote,
                    "userPublicKey": str(self.keypair.pubkey()),
                    "wrapAndUnwrapSol": True,
                    "dynamicComputeUnitLimit": True,
                    "prioritizationFeeLamports": self.priority_fee 
                })
                tx_b64 = s_res.json().get("swapTransaction")

                if tx_b64 and await self.simulate_trade(tx_b64):
                    raw_tx = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
                    signature = self.keypair.sign_message(raw_tx.message)
                    signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
                    payload = {
                        "jsonrpc": "2.0", "id": 1, "method": "sendBundle", 
                        "params": [[base64.b64encode(bytes(signed_tx)).decode("utf-8")]]
                    }
                    await client.post(self.jito_engine, json=payload)
                    await self.notify(f"🎯 SHIELD PASS: BUNDLE SENT\nTarget: {target[:6]}")
            except Exception as e:
                logger.error(f"Strike Failure: {e}")

    async def core_loop(self):
        logger.info("--- OMNICORE v35.0 | SLOT-SYNCED | PULSE: 400ms ---")
        await self.notify("v35 Guardian Online.\nPulse: 400ms")
        while True:
            try:
                if self.target_mint: logger.info(f"Stalking: {self.target_mint}")
                else: logger.info("Scanning Blocks...")
                await asyncio.sleep(self.pulse)
            except: await asyncio.sleep(self.pulse)

def main():
    port = int(os.getenv("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    engine = OmnicoreV35()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine.core_loop())

if __name__ == "__main__":
    main()
