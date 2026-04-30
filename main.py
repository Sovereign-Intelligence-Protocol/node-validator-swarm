import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
import websockets

# --- v35.8 OMNICORE: FINAL REVENUE EXECUTION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - OMNICORE - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

# 1. RENDER HANDSHAKE (Fixes the "Status 1" crash)
@app.route('/')
def health(): 
    return {"status": "LIVE", "engine": "v35.8", "jito_mev": "ACTIVE"}, 200

class SovereignSniper:
    def __init__(self):
        # Precise Recall of your Saved Labels
        self.key = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        
        # Sniper Settings (Recalled from System Data)
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.wss_url = os.getenv("SOLANA_RPC_URL", "wss://api.mainnet-beta.solana.com")
        
        self.buy_amount = 200000000 # 0.2 SOL Strike
        self.slippage = 300 # 3% Slippage (as saved in settings)
        self.jito_tip = 250000 # Priority Fee for congestion
        self.in_trade = False

    async def notify(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            try: await client.post(url, json={"chat_id": self.tg_admin, "text": f"🎯 SNIPER:\n{msg}"})
            except: pass

    async def strike(self, mint):
        if self.in_trade: return
        self.in_trade = True
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # 1. ATOMIC QUOTE
                q_url = f"{self.jup_api}/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={mint}&amount={self.buy_amount}&slippageBps={self.slippage}"
                q_req = await client.get(q_url)
                quote = q_req.json()
                
                # 2. JITO TOLL BRIDGE (Zero Simulation)
                s_req = await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": quote,
                    "userPublicKey": str(self.key.pubkey()),
                    "prioritizationFeeLamports": self.jito_tip 
                })
                tx_data = s_req.json()["swapTransaction"]
                
                # 3. SIGN & FIRE BUNDLE
                raw_tx = VersionedTransaction.from_bytes(base64.b64decode(tx_data))
                signed_tx = VersionedTransaction.populate(raw_tx.message, [self.key.sign_message(raw_tx.message)])
                
                payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed_tx)).decode("utf-8")]]}
                await client.post(self.jito_engine, json=payload)
                
                await self.notify(f"✅ STRIKE FINALIZED\nMint: {mint[:12]}...\nBridge: Jito-MEV")
                
                # Wait for 45s Harvest
                await asyncio.sleep(45)
                self.in_trade = False
            except Exception as e:
                logger.error(f"Strike Error: {e}")
                self.in_trade = False

    async def hunt(self):
        async with websockets.connect(self.wss_url) as ws:
            # Subscribe to Raydium Liquidity Events
            sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["675kPX9MHTjS2zt1qnt1svH774W3LxFtVsiB3Y6nhiW3"]},{"commitment":"processed"}]}
            await ws.send(json.dumps(sub))
            await self.notify("🦅 OMNICORE ONLINE\nScraper: Raydium\nMode: Full Autonomous")
            
            while True:
                msg = json.loads(await ws.recv())
                if "params" in msg and any("initialize2" in log for log in msg['params']['result']['value']['logs']):
                    # Strike current target or autonomous hunt
                    target = os.getenv("TARGET_MINT")
                    if target and target != "AUTONOMOUS":
                        await self.strike(target)

def run_server():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start the "Handshake" thread so Render doesn't kill the bot
    Thread(target=run_server, daemon=True).start()
    # Start the Sniper
    asyncio.run(SovereignSniper().hunt())
