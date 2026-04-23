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
RPC_URL = os.getenv("HELIUS_RPC_URL") or "https://api.mainnet-beta.solana.com"
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_tg_msg(text):
    """Force communication and log the response."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            print(f"📡 Attempting to ping Telegram ID: {TG_CHAT_ID}...")
            resp = await client.post(url, json=payload)
            # This next line is key - it tells us exactly what Telegram said
            print(f"📩 Telegram Response: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ Telegram Connection Failed: {e}")

async def auditor():
    if not all([SEED_WALLET, TG_TOKEN, TG_CHAT_ID]):
        print("❌ CRITICAL: Environment variables are missing in Render settings!")
        return

    print(f"🚀 AUDIT STARTING: Monitoring {SEED_WALLET[:6]}...")
    
    # Send immediate startup ping
    await send_tg_msg(f"⚡ *SOVEREIGN PROTOCOL: ONLINE*\n\n🛰️ *Status:* Live & Monitoring\n🏦 *Wallet:* `{SEED_WALLET[:4]}...{SEED_WALLET[-4:]}`")

    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        pk = Pubkey.from_string(SEED_WALLET)
        res = await client.get_balance(pk)
        last_bal = res.value

        while True:
            try:
                await asyncio.sleep(30)
                new_res = await client.get_balance(pk)
                if new_res.value != last_bal:
                    diff = (new_res.value - last_bal) / 1e9
                    label = "💰 REVENUE" if diff > 0 else "💸 OUTFLOW"
                    msg = f"*{label}*\nAmt: `{diff:.4f} SOL`"
                    await send_tg_msg(msg)
                    last_bal = new_res.value
            except Exception as e:
                print(f"⚠️ Loop error: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(auditor())
