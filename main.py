import os, asyncio, json, httpx
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- TARGETS ---
HOT_WALLET = "junTtoquNLdo4PFeC7JbH6Mzj7aztaTckK4dQrr1tWs"
KRAKEN_DEST = os.getenv("KRAKEN_DESTINATION") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"

# --- SYSTEM STATE ---
stats = {"lifetime": 0.0, "last_bal": 0}

async def notify_discord(amount, event_type, tx_sig="Confirmed"):
    color = 3066993 if "IN" in event_type else 15105570 # Green for In, Orange for Out
    icon = "📥" if "IN" in event_type else "📤"
    
    payload = {
        "embeds": [{
            "title": f"{icon} {event_type}",
            "color": color,
            "description": f"**Amount:** `{amount:.4f} SOL`",
            "fields": [
                {"name": "Current Bridge Balance", "value": f"`{stats['lifetime']:.4f} SOL`", "inline": True},
                {"name": "Destination", "value": "Kraken Vault" if "OUT" in event_type else "Bridge Wallet", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def monitor_everything():
    global stats
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        
        # Initial Sync
        bal_resp = await client.get_balance(pubkey)
        stats["last_bal"] = bal_resp.value
        stats["lifetime"] = stats["last_bal"] / 1e9

        print(f"🚀 Full System Monitor Live for {HOT_WALLET}")

        while True:
            try:
                new_resp = await client.get_balance(pubkey)
                new_bal = new_resp.value
                
                if new_bal != stats["last_bal"]:
                    diff = (new_bal - stats["last_bal"]) / 1e9
                    stats["lifetime"] = new_bal / 1e9
                    
                    if diff > 0:
                        # Categorize the Incoming Money
                        cat = "SUBSCRIPTION" if diff in [2.0, 5.0] else "TOLL IN"
                        await notify_discord(diff, f"{cat} RECEIVED")
                    else:
                        # Track the money going to Kraken
                        await notify_discord(abs(diff), "SWEEP TO KRAKEN (OUT)")
                    
                    stats["last_bal"] = new_bal
                
                await asyncio.sleep(5)
            except Exception as e:
                await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(monitor_everything())
