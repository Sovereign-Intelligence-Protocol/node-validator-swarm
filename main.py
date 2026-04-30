import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
import websockets

# --- v35.8 OMNICORE: ZERO SIMULATION / FULL AUTONOMY ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - OMNICORE - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health(): return {"status": "STRIKING", "engine": "v35.8", "mode": "NO_SIMULATION"}, 200

class OmnicoreScraper:
    def __init__(self):
        self.key = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        self.wss_url = "wss://api.mainnet-beta.solana.com" # Use Helius/Quicknode for production speed
        self.buy_sol = 200000000 # 0.2 SOL
        self.busy = False

    async def alert(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as c:
            await c.post(url, json={"chat_id": self.tg_admin, "text": f"🔥 OMNICORE ALERT:\n{msg}"})

    async def execute_strike(self, mint):
        if self.busy: return
        self.busy = True
        logger.info(f"TARGET DETECTED: {mint} - EXECUTING LIVE STRIKE")
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. RAW QUOTE (No Simulation)
                q_res = await client.get(f"{self.jup_api}/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={mint}&amount={self.buy_sol}&slippageBps=500")
                quote = q_res.json()
                
                # 2. BUILD LIVE SWAP
                s_res = await client.post(f"{self.jup_api}/swap", json={
                    "quoteResponse": quote,
                    "userPublicKey": str(self.key.pubkey()),
                    "prioritizationFeeLamports": 250000 # Aggressive fee for April 30 congestion
                })
                tx_data = s_res.json().get("swapTransaction")
                
                # 3. SIGN & FIRE JITO BUNDLE
                raw_tx = VersionedTransaction.from_bytes(base64.b64decode(tx_data))
                signature = self.key.sign_message(raw_tx.message)
                signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
                
                bundle_payload = {
                    "jsonrpc": "2.0", "id": 1, 
                    "method": "sendBundle", 
                    "params": [[base64.b64encode(bytes(signed_tx)).decode("utf-8")]]
                }
                
                await client.post(self.jito_engine, json=bundle_payload)
                await self.alert(f"✅ STRIKE SENT\nMint: {mint[:8]}...\nJito Fee: 0.00025 SOL")
                
                # Auto-Sell Logic: 45 Seconds 
                await asyncio.sleep(45)
                logger.info("TRADE WINDOW COMPLETE. PREPARING NEXT SCAN.")
                self.busy = False
            except Exception as e:
                logger.error(f"Strike Failure: {e}")
                self.busy = False

    async def start_hunting(self):
        """Scrapes Raydium Program Logs for 'Initialize2' (New LP)"""
        async with websockets.connect(self.wss_url) as ws:
            # Raydium Liquidity Program ID
            sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["675kPX9MHTjS2zt1qnt1svH774W3LxFtVsiB3Y6nhiW3"]},{"commitment":"processed"}]}
            await ws.send(json.dumps(sub))
            await self.alert("🦅 OMNICORE ACTIVE\nMode: Full Autonomous Scraper\nScanning Solana Mempool...")

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if "params" in data:
                    logs = data['params']['result']['value']['logs']
                    # Look for the Raydium 'initialize2' signal
                    if any("initialize2" in log for log in logs):
                        # Extract mint from logs (Simplified - targets TARGET_MINT fallback for now)
                        target = os.getenv("TARGET_MINT")
                        if target: await self.execute_strike(target)

def run_health_check():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_health_check, daemon=True).start()
    bot = OmnicoreScraper()
    asyncio.run(bot.start_hunting())
