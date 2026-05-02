import os, asyncio, base58
from jupiter_python_sdk.jupiter import Jupiter
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

async def main():
    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")

    if not private_key:
        print("❌ Missing PRIVATE_KEY")
        return

    async_client = AsyncClient(rpc_url)
    keypair = Keypair.from_bytes(base58.b58decode(private_key.strip()))
    
    # 1. Execute the $31 Yield Swap once
    jupiter = Jupiter(async_client=async_client, keypair=keypair, quote_api_url="https://quote-api.jup.ag/v6/quote?")
    print("🛡️ S.I.P. Omnicore: Migrating $31 to JitoSOL...")
    
    try:
        tx = await jupiter.swap(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj",
            amount=180000000, 
            slippage_bps=50
        )
        print(f"✅ Yield Swap Complete: {tx}")
    except Exception as e:
        print(f"⚠️ Swap already completed or failed: {e}")

    # 2. The Heartbeat Loop (Keeps Render "Live")
    print("📈 Entering Monitoring Mode (24/7)...")
    while True:
        try:
            bal = (await async_client.get_balance(keypair.pubkey())).value
            print(f"Omnicore Heartbeat: Current Balance {bal} lamports")
            await asyncio.sleep(60) # Checks every minute to keep logs active
        except Exception as e:
            print(f"Heartbeat error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
