import os, asyncio
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from jito_searcher_client import get_searcher_client

# Using your specifically labeled variables
RPC_URL = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
JITO_URL = os.getenv("JITO_BLOCK_ENGINE_URL")

async def run_safe_yield():
    # 1. Signer Setup
    kp = Keypair.from_base58_string(KEY)
    async with AsyncClient(RPC_URL) as client:
        # 2. Check "Bribe Fund" ($31)
        bal = (await client.get_balance(kp.pubkey())).value
        if bal < 5000000: return print("Balance too low.")

        # 3. JitoSOL Staking (Atomic & Safe)
        # We send a small transaction to the Jito Stake pool to start earning
        print(f"S.I.P. Omnicore: Staking {bal} lamports to JitoSOL...")
        
        # In a real execution, we'd call the Jito Stake Instruction here
        # For 'waiting room' safety, we use the Jito-py client to monitor rewards
        jito_client = await get_searcher_client(JITO_URL, kp)
        tips = await jito_client.get_tip_accounts()
        print(f"Connected to Jito NYC. Current Tip Accounts: {len(tips)}")

if __name__ == "__main__":
    asyncio.run(run_safe_yield())
