import os, asyncio, base58, httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# Render Environment Variables
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def send_tg(text):
    """Sends a status update to your Telegram."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": TG_CHAT_ID, "text": text})

async def check_balance():
    """Checks the blockchain for your JitoSOL balance."""
    async with AsyncClient(RPC) as client:
        # Decode key and get public address
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        # Request token account data
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            return f"Balance for {pubkey}: 0 JitoSOL"

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        return f"💰 OMNICORE REPORT\nAccount: {pubkey}\nBalance: {amount:.4f} JitoSOL"

async def main():
    # Immediate confirmation on startup
    await send_tg("🚀 S.I.P. Omnicore is now ONLINE.")
    while True:
        try:
            report = await check_balance()
            await send_tg(report)
            await asyncio.sleep(3600) # Reports every hour
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
