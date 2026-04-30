import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey

# --- PRO-LEVEL INITIALIZATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - OMNICORE-v13.5 - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health():
    return {"status": "ACTIVE", "engine": "Omnicore v13.5", "mode": "PRO-PLAN"}, 200

class OmnicoreEngine:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.vault_addr = os.getenv("VAULT_ADDRESS")
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jito_tip_account = Pubkey.from_string("Cw8CFyM9Fxyqy7yS1f9pTFCBfJC842VfBUE2jGzyq894")
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.pulse = 2 
        self.target_mint = None 

    async def notify(self, message):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json={"chat_id": self.tg_admin, "text": f"🚨 OMNICORE:\n{message}"})
            except Exception as e:
                logger.error(f"TG Error: {e}")

    async def get_swap_tx(self, input_mint, output_mint, amount_lamports):
        async with httpx.AsyncClient() as client:
            try:
                q_url = f"{self.jup_api}/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount_lamports}&slippageBps=100"
                q_res = await client.get(q_url)
                quote_data = q_res.json()
                
                s_res = await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": quote_data,
                    "userPublicKey": str(self.keypair.pubkey()),
                    "wrapAndUnwrapSol": True,
                    "dynamicComputeUnitLimit": True,
                    "prioritizationFeeLamports": 65000 
                })
                return s_res.json().get("swapTransaction")
            except Exception as e:
                logger.error(f"Jupiter Error: {e}")
                return None

    async def fire_jito_bundle(self, swap_tx_b64):
        try:
            raw_tx = VersionedTransaction.from_bytes(base64.b64decode(swap_tx_b64))
            signature = self.keypair.sign_message(raw_tx.message)
            signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
            encoded_tx = base64.b64encode(bytes(signed_tx)).decode("utf-8")
            payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[encoded_tx]]}
            async with httpx.AsyncClient() as client:
                res = await client.post(self.jito_engine, json=payload)
                result = res.json().get("result")
                await self.notify(f"🎯 TARGET ENGAGED!\nJito Bundle ID: {result}")
        except Exception as e:
            logger.error(f"Bundle Error: {e}")

    async def main_loop(self):
        logger.info(f"--- OMNICORE v13.5 ARMED | PULSE: {self.pulse}s ---")
        await self.notify(f"Pro-Engine Online.\nPulse: {self.pulse}s\nReady for Sniper Target.")
        while True:
            try:
                if self.target_mint:
                    logger.info(f"Hunting: {self.target_mint}")
                else:
                    logger.info("Scanning... (No Target Set)")
                await asyncio.sleep(self.pulse)
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                await asyncio.sleep(self.pulse)

def main():
    port = int(os.getenv("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    engine = OmnicoreEngine()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine.main_loop())

if __name__ == "__main__":
    main()
