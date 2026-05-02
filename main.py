import os, asyncio, base58, httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# Your specific manifest labels
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def check_growth():
    async with AsyncClient(RPC) as client:
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        print(f"🔍 S.I.P. Omnicore: Checking Wallet {pubkey}...")

        # 1. Get JitoSOL Token Balance
        # We look for the "Token Account" owned by your wallet that holds JitoSOL
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            print("⚠️ No JitoSOL found yet. The swap might still be processing.")
            return

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        # 2. Get current JitoSOL -> SOL price to show growth
        async with httpx.AsyncClient() as session:
            price_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_price = price_resp.json()['data'][JITOSOL_MINT]['price']

        current_value_in_sol = amount * float(sol_price)
        
        print(f"--- PORTFOLIO REPORT ---")
        print(f"Holding: {amount} JitoSOL")
        print(f"Current Value: {current_value_in_sol:.4f} SOL")
        print(f"Yield: Earning ~8% APY + MEV tips daily.")
        print(f"------------------------")

async def heartbeat():
    while True:
        try:
            await check_growth()
            await asyncio.sleep(300) # Check every 5 minutes
        except Exception as e:
            print(f"Update error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(heartbeat())
