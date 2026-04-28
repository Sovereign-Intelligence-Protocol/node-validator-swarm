import os, asyncio, httpx, base58, json, re
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.async_api import AsyncClient
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from websockets import connect

# --- MAPPED TO YOUR ENVIRONMENTALS ---
RPC_URL = os.getenv("SOLANA_RPC_URL_BASE")
WSS_URL = os.getenv("WSS_URL")
SEED_PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOME_BASE = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
JITO_TIP = float(os.getenv("JITO_TIP_AMOUNT", "0.0005"))
LIVE_MODE = os.getenv("LIVE_TRADING") == "True"

# --- SYSTEM CONSTANTS ---
TOLL_AMOUNT = 0.01
TRADE_SIZE = 0.05  # Standard strike from your $31 balance
PUMP_PROGRAM = "6EF8rrecthR5DkZJv9RKzyuCc91upS8P49fN2fN1"

class SovereignPredator:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(SEED_PRIVATE_KEY)
        self.client = AsyncClient(RPC_URL)
        print(f"⚡ TRIGGER MODE ACTIVE. Seed Wallet: {self.keypair.pubkey()}")

    async def report(self, text):
        url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as c:
            try:
                await c.post(url, json={"chat_id": ADMIN_ID, "text": f"🚀 S.I.P. EXECUTION: {text}"})
            except Exception as e: print(f"Tele Error: {e}")

    async def execute_atomic_bundle(self, target_mint):
        """Fuses Trade + 0.01 SOL Toll + Jito Tip into one strike"""
        print(f"🎯 Striking Mint: {target_mint}")
        
        # 1. The Buy (Seed Wallet)
        buy_ix = transfer(TransferParams(
            from_pubkey=self.keypair.pubkey(),
            to_pubkey=Pubkey.from_string(target_mint),
            lamports=int(TRADE_SIZE * 10**9)
        ))

        # 2. The Toll (Earnings to Home Base)
        toll_ix = transfer(TransferParams(
            from_pubkey=self.keypair.pubkey(),
            to_pubkey=HOME_BASE,
            lamports=int(TOLL_AMOUNT * 10**9)
        ))

        # 3. Jito Tip
        tip_acct = Pubkey.from_string("96g6wio7Wf9mSjCaxqe6SJK4dg3oYWB799S9F8mF1XG6")
        tip_ix = transfer(TransferParams(
            from_pubkey=self.keypair.pubkey(),
            to_pubkey=tip_acct,
            lamports=int(JITO_TIP * 10**9)
        ))

        # Atomic Compilation
        bh = await self.client.get_latest_blockhash()
        msg = MessageV0.try_compile(self.keypair.pubkey(), [buy_ix, toll_ix, tip_ix], [], bh.value.blockhash)
        tx = VersionedTransaction(msg, [self.keypair])
        
        # Fire to Jito Block Engine
        bundle_data = base58.b58encode(bytes(tx)).decode('utf-8')
        payload = {"jsonrpc":"2.0","id":1,"method":"sendBundle","params":[[bundle_data]]}
        
        async with httpx.AsyncClient() as http:
            r = await http.post("https://ny.mainnet.block-engine.jito.wtf/api/v1/bundles", json=payload)
            await self.report(f"Strike Successful! \nMint: {target_mint} \nToll: {TOLL_AMOUNT} SOL sent to Home Base.")

    async def hunt(self):
        """Scanning Helius WSS for Pump.fun Golden Opportunities"""
        async with connect(WSS_URL) as ws:
            sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":[PUMP_PROGRAM]}]}
            await ws.send(json.dumps(sub))
            await self.report("Predator Online. Scanning Mempool...")

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                # Logic: Find new token creations
                log_data = str(data.get('params', {}).get('result', {}).get('value', {}).get('logs', []))
                if "Instruction: Create" in log_data:
                    # Extracting the Mint Address from the log's account keys
                    try:
                        # In 2026 logs, the mint is often the 1st or 2nd account in the creation call
                        # This looks for the unique Pump.fun mint pattern
                        mint_search = re.search(r"[1-9A-HJ-NP-Za-km-z]{32,44}pump", log_data)
                        if mint_search:
                            target_mint = mint_search.group(0)
                            if LIVE_MODE:
                                await self.execute_atomic_bundle(target_mint)
                            else:
                                print(f"🔍 [TEST MODE] Would have struck: {target_mint}")
                    except Exception as e:
                        print(f"Parse Error: {e}")

async def main():
    bot = SovereignPredator()
    await bot.hunt()

if __name__ == "__main__":
    asyncio.run(main())
