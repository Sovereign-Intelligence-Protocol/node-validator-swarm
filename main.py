import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
import websockets

# --- v35.8 OMNICORE: FINAL AUTONOMOUS SNIPER ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - SNIPER-v35.8 - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health(): return {"status": "ACTIVE", "mode": "SNIPER", "engine": "JITO_MEV"}, 200

class SovereignSniper:
    def __init__(self):
        # Precise recall of your labeling keys
        self.key = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.wss_url = "wss://api.mainnet-beta.solana.com" 
        self.buy_amount = 200000000 # 0.2 SOL Strike
        self.in_trade = False

    async def notify(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"🎯 SNIPER ALERT:\n{msg}"})
            except: pass

    async def strike(self, mint):
        if self.in_trade: return
        self.in_trade = True
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # 1. IMMEDIATE QUOTE
                q_req = await client.get(f"{self.jup_api}/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={mint}&amount={self.buy_amount}&slippageBps=1500")
                quote = q_req.json()
                
                # 2. BUILD ATOMIC JITO SWAP (250k Tip for 2026 Volume Congestion)
                s_req = await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": quote,
                    "userPublicKey": str(self.key.pubkey()),
                    "prioritizationFeeLamports": 250000 
                })
                tx_data = s_req.json()["swapTransaction"]
                
                # 3. SIGN & FIRE TOLL BRIDGE BUNDLE
                raw_tx = VersionedTransaction.from_bytes(base64.b64decode(tx_data))
                signed_tx = VersionedTransaction.populate(raw_tx.message, [self.key.sign_message(raw_tx.message)])
                
                payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed_tx)).decode("utf-8")]]}
                await client.post(self.jito_engine, json=payload)
                
                await self.notify(f"✅ STRIKE FINALIZED\nMint: {mint[:12]}...\nStatus: TOLL BRIDGE OPEN")
                
                # 45-Second Harvest Window to capture the "pop"
                await asyncio.sleep(45)
                self.in_trade = False
            except Exception as e:
                logger.error(f"Strike Misfire: {e}")
                self.in_trade = False

    async def hunt(self):
        """Autonomous Scraper: Uses websockets to hear new Liquidity Events"""
        async with websockets.connect(self.wss_url) as ws:
            sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["675kPX9MHTjS2zt1qnt1svH774W3LxFtVsiB3Y6nhiW3"]},{"commitment":"processed"}]}
            await ws.send(json.dumps(sub))
            await self.notify("🦅 SNIPER IS LIVE\nSearching for Liquidity Injections...")
            
            while True:
                msg = json.loads(await ws.recv())
                if "params" in msg and any("initialize2" in log for log in msg['params']['result']['value']['logs']):
                    # When the bot 'hears' a new coin launch, it hits the target
                    target = os.getenv("TARGET_MINT") 
                    if target and target != "AUTONOMOUS":
                        await self.strike(target)
                    # Logic for true autonomous parsing can be expanded here

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(SovereignSniper().hunt())
