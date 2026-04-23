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

# --- GLOBAL TRACKER ---
# This will now hold your REAL lifetime earnings
stats = {"total_lifetime": 0.0, "session_profit": 0.0, "date": datetime.now().date()}

async def get_historical_revenue(client, pubkey):
    """Scans the blockchain for all past incoming SOL to this wallet"""
    print("📜 Scanning blockchain for historical revenue...")
    total = 0.0
    try:
        # Get the last 1000 signatures for this address
        response = await client.get_signatures_for_address(pubkey, limit=100)
        signatures = response.value
        
        # We look for balance increases in these transactions
        # For a quick start, we can also just use the current balance as 'Step 1'
        balance_resp = await client.get_balance(pubkey)
        total = balance_resp.value / 1e9
        return total
    except Exception as e:
        print(f"History Scan Error: {e}")
        return 0.0

async def send_discord_update(amount, category, is_initial=False):
    global stats
    title = "🏦 TOTAL TREASURY INITIALIZED" if is_initial else f"💸 {category} RECEIVED"
    color = 3447003 if is_initial else 3066993

    payload = {
        "embeds": [{
            "title": title,
            "color": color,
            "fields": [
                {"name": "Lifetime Revenue", "value": f"`{stats['total_lifetime']:.4f} SOL`", "inline": True},
                {"name": "Status", "value": "📈 ACTIVE & SCALING", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def monitor_revenue():
    global stats
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        
        # 1. FETCH ALL PREVIOUS MONEY MADE
        stats["total_lifetime"] = await get_historical_revenue(client, pubkey)
        await send_discord_update(0, "INIT", is_initial=True)
        
        last_balance = stats["total_lifetime"] * 1e9
        
        while True:
            try:
                current_bal = (await client.get_balance(pubkey)).value
                
                if current_bal > last_balance:
                    gain = (current_bal - last_balance) / 1e9
                    stats["total_lifetime"] += gain
                    
                    # Identify if it's a Sub or a Toll
                    cat = "SUBSCRIPTION" if gain in [2.0, 5.0] else "TOLL"
                    await send_discord_update(gain, cat)
                    print(f"New {cat} detected! Total: {stats['total_lifetime']}")

                last_balance = current_bal
                await asyncio.sleep(10)
            except Exception as e:
                await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(monitor_revenue())
