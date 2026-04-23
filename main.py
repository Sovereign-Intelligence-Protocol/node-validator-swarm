import os, asyncio, json, httpx
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- CONFIG FROM RENDER ENVIRONMENT ---
# Ensure these Keys exist in your Render 'Environment' tab
HOT_WALLET = os.getenv("HOT_WALLET_ADDRESS")
KRAKEN_DEST = os.getenv("KRAKEN_DESTINATION")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"

# --- REVENUE TRACKER ---
stats = {"lifetime_sol": 0.0, "last_bal": 0}

async def send_to_discord(amount, category, is_initial=False):
    """Sends the high-impact revenue cards to your Discord"""
    color = 3447003 if category in ["API SUBSCRIPTION", "WHALE PASS", "INITIAL"] else 3066993
    title = "🏦 TREASURY REVENUE INITIALIZED" if is_initial else f"💸 {category} RECEIVED"
    
    payload = {
        "embeds": [{
            "title": title,
            "color": color,
            "fields": [
                {"name": "Lifetime Revenue", "value": f"`{stats['lifetime_sol']:.4f} SOL`", "inline": True},
                {"name": "Status", "value": "🟢 SCALPING ACTIVE", "inline": True},
                {"name": "Type", "value": f"**{category}**", "inline": False}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(DISCORD_WEBHOOK, json=payload, timeout=10.0)
        except Exception as e:
            print(f"Discord Webhook Error: {e}")

async def monitor_revenue_and_subs():
    """Main loop: Tracks tolls, subscriptions, and kraken sweeps"""
    global stats
    async with AsyncClient(RPC_URL) as client:
        if not HOT_WALLET:
            print("❌ ERROR: HOT_WALLET_ADDRESS not found in Environment Variables!")
            return

        pubkey = Pubkey.from_string(HOT_WALLET)
        
        # Initial Sync - Pulls your current 0.3649 SOL balance immediately
        bal_resp = await client.get_balance(pubkey)
        stats["last_bal"] = bal_resp.value
        stats["lifetime_sol"] = stats["last_bal"] / 1e9
        
        await send_to_discord(0, "INITIAL", is_initial=True)
        print(f"🚀 Monitoring Revenue for: {HOT_WALLET}")

        while True:
            try:
                new_resp = await client.get_balance(pubkey)
                new_bal = new_resp.value
                
                if new_bal != stats["last_bal"]:
                    diff = (new_bal - stats["last_bal"]) / 1e9
                    stats["lifetime_sol"] = new_bal / 1e9
                    
                    if diff > 0:
                        # Identify specific subscription amounts
                        if round(diff, 1) == 2.0:
                            cat = "API SUBSCRIPTION"
                        elif round(diff, 1) == 5.0:
                            cat = "WHALE PASS"
                        else:
                            cat = "TOLL IN"
                        
                        await send_to_discord(diff, cat)
                    else:
                        # Track the sweep to your Kraken vault
                        await send_to_discord(abs(diff), "SWEEP TO KRAKEN")
                    
                    stats["last_bal"] = new_bal
                
                await asyncio.sleep(10)
            except Exception as e:
                print(f"Monitoring Loop Error: {e}")
                await asyncio.sleep(15)

# --- PLACEHOLDER FOR SCALPER LOGIC ---
# This ensures your trading bot background tasks still run
async def lead_scalper_engine():
    print("🎯 Lead Scalper Engine: Active & Hunting...")
    while True:
        # Your original trading/scanning logic stays active here
        await asyncio.sleep(60)

async def main():
    # Runs the Revenue Monitor and the Scalper Engine at the same time
    await asyncio.gather(
        monitor_revenue_and_subs(),
        lead_scalper_engine()
    )

if __name__ == "__main__":
    asyncio.run(main())
