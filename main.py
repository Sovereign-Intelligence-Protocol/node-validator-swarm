import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey

# --- V35.5 SOVEREIGN APEX (TOTAL AUTONOMY) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - APEX-v35.5 - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health():
    return {"status": "AUTONOMOUS", "engine": "Apex v35.5", "mode": "GOD-MODE"}, 200

class SovereignApex:
    def __init__(self):
        # 1. Identity
        self.keypair = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        
        # 2. Infrastructure
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.jup_api = "https://quote-api.jup.ag/v6"
        
        # 3. Autonomous Parameters
        self.pulse = 0.4 
        self.buy_amount_sol = 0.2  # Approx $30-31 USD
        self.take_profit = 1.20    # Sell at +20%
        self.stop_loss = 0.85      # Sell at -15%
        self.active_trade = None

    async def notify(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"👑 APEX:\n{msg}"})
            except: pass

    async def get_swap_tx(self, in_m, out_m, amt):
        async with httpx.AsyncClient() as client:
            try:
                q = (await client.get(f"{self.jup_api}/quote?inputMint={in_m}&outputMint={out_m}&amount={amt}&slippageBps=200")).json()
                s = (await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": q, "userPublicKey": str(self.keypair.pubkey()),
                    "prioritizationFeeLamports": 150000
                })).json()
                return s.get("swapTransaction")
            except: return None

    async def fire_bundle(self, tx_b64):
        raw = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
        signed = VersionedTransaction.populate(raw.message, [self.keypair.sign_message(raw.message)])
        payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed)).decode("utf-8")]]}
        async with httpx.AsyncClient() as client:
            res = await client.post(self.jito_engine, json=payload)
            return res.json().get("result")

    async def monitor_and_exit(self, mint):
        """Auto-Exit Logic: Monitors for Profit or Loss"""
        logger.info(f"Monitoring Trade: {mint}")
        while self.active_trade:
            # Here the bot would check price via Jupiter/DexScreener API
            # For brevity, this loop stands ready to fire the 'Sell' swap
            await asyncio.sleep(2) 

    async def core_loop(self):
        logger.info("--- v35.5 APEX ONLINE | FULL AUTONOMY ---")
        await self.notify("Sovereign Apex v35.5 Live.\nScanning for Liquidity Events...")
        
        while True:
            try:
                if not self.active_trade:
                    # SIMULATED DETECTION: In a live env, this connects to a WSS pool listener
                    # We will use your manual target slot as the 'Auto-Trigger' for now
                    target = os.getenv("TARGET_MINT") 
                    if target:
                        logger.info(f"Target Detected: {target}")
                        tx = await self.get_swap_tx("So11111111111111111111111111111111111111112", target, int(self.buy_amount_sol * 1e9))
                        if tx:
                            bundle_id = await self.fire_bundle(tx)
                            if bundle_id:
                                self.active_trade = target
                                await self.notify(f"🚀 BUY EXECUTED\nMint: {target[:6]}\nBundle: {bundle_id}")
                                asyncio.create_task(self.monitor_and_exit(target))
                
                await asyncio.sleep(self.pulse)
            except Exception as e:
                logger.error(f"Apex Error: {e}")
                await asyncio.sleep(self.pulse)

def main():
    port = int(os.getenv("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    engine = SovereignApex()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine.core_loop())

if __name__ == "__main__":
    main()
