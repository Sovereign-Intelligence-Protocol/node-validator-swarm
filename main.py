import os
import asyncio
import threading
import base58
import httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- PHASE 1: THE HEARTBEAT ---
# This stops the "Port scan timeout" and reboot loops
app = Flask(__name__)

@app.route('/')
def health():
    return "OMNICORE: Operational", 200

def run_heartbeat():
    # Render requires binding to the environment PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Launch Flask in a separate thread so it doesn't block the bot
threading.Thread(target=run_heartbeat, daemon=True).start()

# --- PHASE 2: TELEGRAM & MONITORING ---
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def send_tg(text):
    """Sends a direct notification to your Telegram."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            print(f"Telegram Error: {e}")

async def get_growth_report():
    """Calculates balance and current value."""
    async with AsyncClient(RPC) as client:
        # Decode the wallet key
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        # Check Token Account for JitoSOL
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            return f"🛡️ S.I.P. Omnicore: Monitoring {pubkey[:6]}... (No JitoSOL found)"

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        # Fetch current price via Jupiter API
        async with httpx.AsyncClient() as session:
            p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_price = float(p_resp.json()['data'][JITOSOL_MINT]['price'])

        return (
            f"📈 OMNICORE GROWTH REPORT\n"
            f"Account: {pubkey}\n"
            f"Holding: {amount:.4f} JitoSOL\n"
            f"Current Value: {amount * sol_price:.4f} SOL\n"
            f"Status: Predator Engaged"
        )

async def main():
    # Send an immediate alert so you know the bot is stable
    await send_tg("🚀 S.I.P. Omnicore: Predator Engaged. System is Live and Monitoring.")
    
    while True:
        try:
            report = await get_growth_report()
            await send_tg(report)
            
            # Reports every hour; internal heartbeat is handled by Flask
            await asyncio.sleep(3600) 
        except Exception as e:
            print(f"Operational Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
