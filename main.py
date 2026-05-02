import os, asyncio, base58, httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# Config from your Render Environment Variables
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

async def check_growth():
    async with AsyncClient(RPC) as client:
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            return "🔍 Monitoring: Checking for JitoSOL account..."

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        async with httpx.AsyncClient() as session:
            p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_val = float(p_resp.json()['data'][JITOSOL_MINT]['price'])

        report = (
            f"📈 OMNICORE GROWTH REPORT\n"
            f"Balance: {amount:.4f} JitoSOL\n"
            f"Value: {amount * sol_val:.4f} SOL\n"
            f"Status: Live & Earning Yield"
        )
        return report

async def main():
    await send_tg_message("🚀 S.I.P. Omnicore is now ONLINE on Render.")
    while True:
        try:
            report = await check_growth()
            await send_tg_message(report)
            await asyncio.sleep(3600) # Sends an update once every hour
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
