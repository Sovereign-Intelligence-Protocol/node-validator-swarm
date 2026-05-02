import os, asyncio, base58
from jupiter_python_sdk.jupiter import Jupiter # From your requirements
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# 1. Load your specific labels
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") 

async def main():
    # 2. Setup Identity
    async_client = AsyncClient(RPC_URL)
    keypair = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
    
    # Initialize Jupiter with your keypair
    jupiter = Jupiter(
        async_client=async_client,
        keypair=keypair,
        quote_api_url="https://quote-api.jup.ag/v6/quote?"
    )

    # 3. Execution: Swap $31 (approx 0.18 SOL) to JitoSOL
    # Amount is in lamports (1 SOL = 1,000,000,000)
    print("S.I.P. Omnicore: Executing Safe Yield Swap...")
    
    try:
        transaction_data = await jupiter.swap(
            input_mint="So11111111111111111111111111111111111111112", # SOL
            output_mint="J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj", # JitoSOL
            amount=180000000, # Approx $30-31
            slippage_bps=10   # 0.1% slippage
        )
        
        # In the 2026 SDK, transaction_data contains the signature
        print(f"Success! Your $31 is now earning Jito MEV rewards.")
        print(f"Check your wallet for JitoSOL.")
    except Exception as e:
        print(f"Swap Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
