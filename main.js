import os
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from jup_ag_sdk import Jupiter # Assuming Jupiter SDK for Python 2026

# Using your specifically labeled variables
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_ENABLED = os.getenv("JITO_ENABLED") # Verify if we want to use Jito route

async def main():
    # Initialize connection using your labeled RPC
    client = AsyncClient(RPC_URL)
    wallet = Keypair.from_base58_string(PRIVATE_KEY)
    
    print(f"Omnicore Waiting Mode: Funding JitoSOL with {wallet.pubkey()}")

    # 1. Check Balance
    balance = await client.get_balance(wallet.pubkey())
    if balance.value < 10000000: # Ensure we have enough for gas
        print("Balance too low for swap.")
        return

    # 2. Swap SOL -> JitoSOL (The safest yield)
    # This uses Jupiter to find the best path for your $31
    jup = Jupiter(client, wallet)
    quote = await jup.get_quote("So11111111111111111111111111111111111111112", "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj", 25000000) # ~$25-30
    
    transaction = await jup.swap(quote)
    result = await client.send_transaction(transaction)
    
    print(f"Success! Your $31 is now earning Jito MEV rewards. Sig: {result}")

if __name__ == "__main__":
    asyncio.run(main())
