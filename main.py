import os
import asyncio
import threading
import base58
import httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- 1. HEARTBEAT SETUP (Stops Render Restarts) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "S.I.P. Omnicore: ONLINE", 200

def run_heartbeat():
    try:
        # Bind to Render's dynamic port immediately
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Heartbeat server failed: {e}")

# Start the server thread immediately
threading.Thread(target=run_heartbeat, daemon=True).start()

# --- 2. CONFIGURATION ---
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

async def send_tg(text):
    """Sends a notification with error logging for Render."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Telegram variables are missing from Environment tab.")
        return
        
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code != 200:
                print(f"Telegram API Error: {response.status_code} - {response.text}")
            else:
                print("Telegram message sent successfully.")
        except Exception as e:
            print(f"Failed to connect to Telegram: {e}")

async def get_growth_report():
    """Calculates balance and current JitoSOL value."""
    async with AsyncClient(RPC) as client:
        # Decode the key and get pubkey
        raw_key = KEY.strip() if KEY else ""
        kp = Keypair.from_bytes(base58.b58decode(raw_key))
        pubkey = kp.pubkey()
        
        # Check Token Account
        resp = await client.get_token_accounts_by_owner(
            pubkey, 
            {"mint": Pubkey.from_string(JITOSOL_MINT)},
            encoding="jsonParsed"
        )
        
        if not resp.value:
            return f"🛡️ S.I.P. Omnicore\nAccount: {pubkey}\nStatus: Monitoring (No JitoSOL detected)"

        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        
        # Get Price via Jupiter
        async with httpx.AsyncClient() as session:
            p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            sol_price = float(p_resp.json()['data'][JITOSOL_MINT]['price'])

        return (
            f"📈 OMNICORE GROWTH REPORT\n"
            f"Account: {pubkey}\n"
            f"Holding: {amount:.4f} JitoSOL\n"
            f"SOL Value: {amount * sol_price:.4f} SOL\n"
            f"Status: Predator Engaged"
        )

async def main():
    # Initial alert to confirm the bot is stable and live
    print("System initializing...")
    await send_tg("🚀 S.I.P. Omnicore: Predator Engaged. System is stable and monitoring growth.")
    
    while True:
        try:
            report = await get_growth_report()
            await send_tg(report)
            # Send report every hour
            await asyncio.sleep(3600) 
        except Exception as e:
            print(f"Loop error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
