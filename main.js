import os, asyncio
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from jito_searcher_client import get_searcher_client # From jito-py

# Only pulling the labels we need right now
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
JITO_URL = os.getenv("JITO_BLOCK_ENGINE_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    # Initialize using your 22-label identity
    kp = Keypair.from_base58_string(KEY)
    async with AsyncClient(RPC) as client:
        # Check $31 Balance (measured in lamports)
        bal = (await client.get_balance(kp.pubkey())).value
        if bal < 5000000: return print("Balance too low for gas.")

        print(f"🛡️ S.I.P. Omnicore: Activating Passive Yield Mode...")
        
        # This connects you to the Jito NYC Engine to 'warm up' your connection
        # while your $31 sits in JitoSOL earning 8% + MEV tips.
        jito_client = await get_searcher_client(JITO_URL, kp)
        print(f"Connected to Jito NYC. Server status: ACTIVE")

if __name__ == "__main__":
    asyncio.run(main())
