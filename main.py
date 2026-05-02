import os
import asyncio
import threading
import base58
import httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- 1. THE HEARTBEAT (STOPS RENDER REBOOTS) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "S.I.P. Omnicore: Operational", 200

def run_heartbeat():
    # Satisfies Render's port scan to keep the service "Live"
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Start the web server in a background thread
threading.Thread(target=run_heartbeat, daemon=True).start()

# --- 2. CONFIGURATION ---
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def send_tg(text):
    """Sends a notification to your Telegram."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            print(f"Telegram Notification Error: {e}")

async def get_growth_report():
    """Fetches JitoSOL balance and current SOL value."""
    async with AsyncClient(RPC) as client:
        # Reconstruct wallet address
        kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
        pubkey = kp.pubkey()
        
        # Check for JitoSOL token account
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            return f"🛡️ Monitoring {pubkey[:6]}...: No JitoSOL detected."

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        # Get JitoSOL price in SOL from Jupiter API
        async with httpx.AsyncClient() as session:
            p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_val = float(p_resp.json()['data'][JITOSOL_MINT]['price'])

        return (
            f"📈 OMNICORE GROWTH REPORT\n"
            f"Account: {pubkey}\n"
            f"Holding: {amount:.4f} JitoSOL\n"
            f"Value: {amount * sol_val:.4f} SOL\n"
            f"Status: Predator Engaged"
        )

async def main():
    # Confirm system is online once the loop starts
    await send_tg("🚀 S.I.P. Omnicore: Predator Engaged. Monitor is stable.")
    
    while True:
        try:
            report = await get_growth_report()
            await send_tg(report)
            
            # 120s loop for internal persistence, but TG report once per hour
            # Change 3600 to 60 if you want updates every minute for testing
            await asyncio.sleep(3600) 
        except Exception as e:
            print(f"Operational Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
