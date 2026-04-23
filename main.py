import os, asyncio, json, httpx
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- HARD-CODED CONFIG (CRITICAL FIX) ---
HOT_WALLET = "junTtoquNLdo4PFeC7JbH6Mzj7aztaTckK4dQrr1tWs" 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"

# --- GLOBAL TRACKER ---
stats = {"total_lifetime": 0.0, "tolls": 0, "subs": 0, "date": datetime.now().date()}

async def send_discord_update(amount, category, is_initial=False):
    global stats
    
    # Visual Logic: Blue for Subscriptions, Green for Tolls/Initial
    color = 3447003 if category in ["API SUBSCRIPTION", "WHALE PASS", "INITIAL"] else 3066993
    title = "🏦 TREASURY REVENUE INITIALIZED" if is_initial else f"💸 {category} RECEIVED"
    
    payload = {
        "embeds": [{
            "title": title,
            "color": color,
            "fields": [
                {"name": "Lifetime Revenue", "value": f"`{stats['total_lifetime']:.4f} SOL`", "inline": True},
                {"name": "Current Status", "value": "📈 ACTIVE & SCALING", "inline": True},
                {"name": "Type", "value": f"**{category}**", "inline": False}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(DISCORD_WEBHOOK, json=payload, timeout=10.0)
        except Exception as e:
            print(f"Discord Error: {e}")

async def monitor_revenue():
    global stats
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        
        # 1. Boot up: Grab the existing money you've made
        print(f"🔗 Syncing Wallet: {HOT_WALLET}")
        current_bal_raw = (await client.get_balance(pubkey)).value
        stats["total_lifetime"] = current_bal_raw / 1e9
        
        # 2. Immediate proof to Discord
        await send_discord_update(0, "INITIAL", is_initial=True)
        
        last_balance = current_bal_raw
        
        while True:
            try:
                # Reset Daily logic if needed (optional)
                if datetime.now().date() != stats["date"]:
                    stats["date"] = datetime.now().date()

                current_bal = (await client.get_balance(pubkey)).value
                
                if current_bal > last_balance:
                    gain = (current_bal - last_balance) / 1e9
                    stats["total_lifetime"] += gain
                    
                    # Identify Revenue Type
                    if gain == 2.0:
                        cat = "API SUBSCRIPTION"
                    elif gain == 5.0:
                        cat = "WHALE PASS"
                    else:
                        cat = "TOLL"
                    
                    await send_discord_update(gain, cat)
                    print(f"Verified {cat}: {gain} SOL")

                last_balance = current_bal
                await asyncio.sleep(10) # 10-second heartbeat
            except Exception as e:
                print(f"Loop Error: {e}")
                await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(monitor_revenue())
