import os
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

load_dotenv()

# --- CONFIG ---
# These pull from your Render Environment Variables
RPC_URL = os.getenv("HELIUS_RPC_URL") or "https://api.mainnet-beta.solana.com"
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_tg_msg(text):
    """Sends a direct signal to the Sovereign Command Center on Telegram."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                print(f"❌ Telegram API Error: {resp.text}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

async def auditor():
    # Safety check for environment variables
    if not all([SEED_WALLET, TG_TOKEN, TG_CHAT_ID]):
        print("❌ ERROR: Missing TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, or HOT_WALLET_ADDRESS in Render!")
        return

    print(f"🚀 AUDIT START: Monitoring {SEED_WALLET[:6]}...")
    
    # Startup Notification
    await send_tg_msg(
        f"⚡ *SOVEREIGN PROTOCOL: ONLINE*\n\n"
        f"🏦 *Destination:* Kraken Account\n"
        f"🛰️ *Status:* Monitoring Live\n"
        f"⏰ *Time:* `{datetime.now().strftime('%H:%M:%S')} UTC`"
    )

    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        try:
            pk = Pubkey.from_string(SEED_WALLET)
            res = await client.get_balance(pk)
            last_bal = res.value
        except Exception as e:
            print(f"❌ Solana Connection Failed: {e}")
            last_bal = 0

        while True:
            try:
                await asyncio.sleep(30) # Efficient check every 30 seconds
                new_res = await client.get_balance(pk)
                
                if new_res.value != last_bal:
                    diff = (new_res.value - last_bal) / 1e9
                    label = "💰 REVENUE" if diff > 0 else "💸 OUTFLOW"
                    
                    msg = (
                        f"*{label} DETECTED*\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🔹 *Change:* `{diff:.4f} SOL`\n"
                        f"🏦 *Kraken Total:* `{new_res.value/1e9:.4f} SOL`"
                    )
                    await send_tg_msg(msg)
                    last_bal = new_res.value
                    
            except Exception as e:
                print(f"⚠️ Loop Warning: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(auditor())
    except Exception as e:
        print(f"❌ Fatal Crash: {e}")
