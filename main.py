import os, asyncio, base58, httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# Configuration from your Render Environment Variables
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def send_telegram(text):
    """Sends a simple status update to your phone."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            print(f"Telegram failed: {e}")

async def get_balance():
    """Checks the blockchain for your JitoSOL balance."""
    async with AsyncClient(RPC) as client:
        # Securely recreate your wallet address from the private key
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        # Look specifically for the JitoSOL token account
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            return f"Checked {pubkey}: No JitoSOL found yet."

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        # Get the current value of JitoSOL in SOL terms
        async with httpx.AsyncClient() as session:
            p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_val = float(p_resp.json()['data'][JITOSOL_MINT]['price'])

        return (
            f"💰 OMNICORE BALANCE REPORT\n"
            f"Account: {pubkey}\n"
            f"Balance: {amount:.4f} JitoSOL\n"
            f"SOL Value: {amount * sol_val:.4f} SOL\n"
            f"Status: Actively earning yield."
        )

async def main():
    # Let you know the bot started successfully
    await send_telegram("🚀 S.I.P. Omnicore has started on Render.")
    
    while True:
        try:
            # Check the balance and send it to you
            report = await get_balance()
            await send_telegram(report)
            
            # Wait 1 hour before the next update to keep logs clean
            await asyncio.sleep(3600) 
        except Exception as e:
            print(f"Loop error: {e}")
            await asyncio.sleep(60) # Wait a minute if something fails

if __name__ == "__main__":
    asyncio.run(main())
