import os, asyncio, base58, httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# Your specific manifest labels
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def check_portfolio():
    async with AsyncClient(RPC) as client:
        # Decode key and find your wallet address
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        # Look for the JitoSOL token account
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            print(f"🔍 Checking {pubkey}: No JitoSOL found yet.")
            return

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        # Get live growth data from Jupiter
        async with httpx.AsyncClient() as session:
            price_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_price = float(price_resp.json()['data'][JITOSOL_MINT]['price'])

        print(f"\n--- S.I.P. OMNICORE GROWTH REPORT ---")
        print(f"Wallet: {pubkey}")
        print(f"Holding: {amount:.4f} JitoSOL")
        print(f"Value in SOL: {amount * sol_price:.4f} SOL")
        print(f"Status: Earning ~8% APY + MEV tips")
        print(f"------------------------------------\n")

async def main():
    while True:
        try:
            await check_portfolio()
            await asyncio.sleep(60) # Reports every minute to keep Render Green
        except Exception as e:
            print(f"Report Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
