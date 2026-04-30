import asyncio, os, httpx, base58, logging, base64, json
from flask import Flask
from threading import Thread
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
import websockets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - OMNICORE - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def health(): return {"status": "LIVE", "engine": "v35.8", "target": "AUTONOMOUS"}, 200

class OmnicoreScraper:
    def __init__(self):
        self.key = Keypair.from_base58_string(os.getenv("PRIVATE_KEY"))
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_admin = os.getenv("TELEGRAM_ADMIN_ID")
        self.jup_api = "https://quote-api.jup.ag/v6"
        self.jito_engine = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
        # Using a reliable WSS for the 2026 volume surge
        self.wss_url = "wss://api.mainnet-beta.solana.com" 
        self.buy_sol = 200000000 # 0.2 SOL
        self.busy = False

    async def alert(self, msg):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        async with httpx.AsyncClient() as c:
            try: await c.post(url, json={"chat_id": self.tg_admin, "text": f"🦅 OMNICORE:\n{msg}"})
            except: pass

    async def strike(self, mint):
        if self.busy: return
        self.busy = True
        async with httpx.AsyncClient() as client:
            try:
                # 1. LIVE QUOTE
                q = (await client.get(f"{self.jup_api}/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={mint}&amount={self.buy_sol}&slippageBps=1000")).json()
                # 2. SIGN & BUNDLE (250k lamport Jito Tip for Meta-news congestion)
                s = (await client.post(f"{self.jup_api}/swap", json={"quoteResponse": q, "userPublicKey": str(self.key.pubkey()), "prioritizationFeeLamports": 250000})).json()
                raw = VersionedTransaction.from_bytes(base64.b64decode(s["swapTransaction"]))
                signed = VersionedTransaction.populate(raw.message, [self.key.sign_message(raw.message)])
                bundle = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[base64.b64encode(bytes(signed)).decode("utf-8")]]}
                await client.post(self.jito_engine, json=bundle)
                await self.alert(f"✅ STRIKE EXECUTED\nMint: {mint[:10]}")
                await asyncio.sleep(45) # 45s harvest window
                self.busy = False
            except Exception as e:
                logger.error(f"Strike Error: {e}")
                self.busy = False

    async def hunt(self):
        async with websockets.connect(self.wss_url) as ws:
            # Listening to Raydium (675kPX...) for new liquidity
            await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["675kPX9MHTjS2zt1qnt1svH774W3LxFtVsiB3Y6nhiW3"]},{"commitment":"processed"}]}))
            await self.alert("🦅 HUNTING ACTIVE\nMode: Autonomous\nNetwork: Solana Mainnet")
            while True:
                msg = json.loads(await ws.recv())
                if "params" in msg and any("initialize2" in log for log in msg['params']['result']['value']['logs']):
                    # When a new pool hits, we strike the fallback or parsed mint
                    target = os.getenv("TARGET_MINT")
                    if target: await self.strike(target)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()
    asyncio.run(OmnicoreScraper().hunt())
