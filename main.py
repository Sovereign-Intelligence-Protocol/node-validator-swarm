import os, asyncio, json, httpx
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- CONFIG ---
HOT_WALLET = "junT...1tWs" 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"

# --- REVENUE TRACKER ---
stats = {"total": 0.0, "tolls": 0, "subs": 0, "date": datetime.now().date()}

async def send_discord_update(amount, category):
    global stats
    stats["total"] += amount
    
    # Determine Color: Blue for Subs, Green for Tolls
    color = 3447003 if category != "TOLL" else 3066993
    icon = "🎫" if category == "SUBSCRIPTION" else "💸"

    payload = {
        "embeds": [{
            "title": f"{icon} {category} RECEIVED",
            "color": color,
            "fields": [
                {"name": "Amount", "value": f"`+{amount:.2f} SOL`", "inline": True},
                {"name": "Daily Revenue", "value": f"`{stats['total']:.2f} SOL`", "inline": True},
                {"name": "Type", "value": f"**{category}**", "inline": False}
            ],
            "footer": {"text": f"Sovereign Intel | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def monitor_revenue():
    global stats
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        last_balance = (await client.get_balance(pubkey)).value
        
        while True:
            try:
                # Reset at midnight
                if datetime.now().date() != stats["date"]:
                    stats = {"total": 0.0, "tolls": 0, "subs": 0, "date": datetime.now().date()}

                current_bal = (await client.get_balance(pubkey)).value
                
                if current_bal > last_balance:
                    gain = (current_bal - last_balance) / 1e9
                    
                    # CATEGORY LOGIC
                    if gain == 2.0:
                        cat = "API SUBSCRIPTION"
                        stats["subs"] += 1
                    elif gain == 5.0:
                        cat = "WHALE PASS"
                        stats["subs"] += 1
                    else:
                        cat = "TOLL"
                        stats["tolls"] += 1
                    
                    await send_discord_update(gain, cat)
                    print(f"Verified {cat}: {gain} SOL")

                last_balance = current_bal
                await asyncio.sleep(5)
            except Exception as e:
                await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(monitor_revenue())
