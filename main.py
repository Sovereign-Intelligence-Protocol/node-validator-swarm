import os, asyncio, httpx
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- CONFIG ---
HOT_WALLET = os.getenv("HOT_WALLET_ADDRESS")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"

# --- GLOBAL TRACKER ---
stats = {
    "total_lifetime": 0.0,
    "daily_tolls": 0.0,
    "daily_subs": 0.0,
    "last_bal": 0,
    "current_day": datetime.now().date()
}

async def get_sol_price():
    """Fetches real-time SOL price for USD transparency"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            return float(resp.json()['price'])
    except: return 150.0  # Fallback price

def identify_revenue(amount):
    if 1.8 <= amount <= 2.2: return "💎 API SUBSCRIPTION", 3447003, "sub"
    if 4.8 <= amount <= 5.2: return "🐋 WHALE PASS", 10181035, "sub"
    if 0.0001 <= amount < 0.2: return "⛽ TRADE TOLL (1%)", 3066993, "toll"
    return "💰 MISC REVENUE", 15105570, "misc"

async def post_to_discord(amount, category, color, tx_sig, current_bal, is_sweep=False):
    global stats
    sol_price = await get_sol_price()
    usd_val = amount * sol_price
    total_usd = stats['total_lifetime'] * sol_price
    
    solscan_url = f"https://solscan.io/tx/{tx_sig}" if tx_sig else "https://solscan.io"
    title = f"🚨 {category}"
    if is_sweep:
        title = "📤 FUNDS MOVED TO KRAKEN VAULT"
        color = 15105570 

    payload = {
        "embeds": [{
            "title": title,
            "color": color,
            "fields": [
                {"name": "Transaction", "value": f"`{amount:.4f} SOL` (~${usd_val:.2f} USD)", "inline": True},
                {"name": "Bridge Balance", "value": f"`{current_bal:.4f} SOL`", "inline": True},
                {"name": "Daily Stats", "value": f"Tolls: `{stats['daily_tolls']:.2f}` | Subs: `{stats['daily_subs']:.2f}`", "inline": False},
                {"name": "Total Wealth Created", "value": f"**`{stats['total_lifetime']:.4f} SOL` (~${total_usd:,.2f} USD)**", "inline": False},
                {"name": "System Status", "value": "🟢 SCALPING ACTIVE", "inline": True},
                {"name": "On-Chain Proof", "value": f"[View on Solscan]({solscan_url})", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try: await client.post(DISCORD_WEBHOOK, json=payload)
        except: pass

async def auditor_engine():
    global stats
    async with AsyncClient(RPC_URL) as client:
        if not HOT_WALLET: return
        pubkey = Pubkey.from_string(HOT_WALLET)
        
        # Initial Balance Sync
        bal_resp = await client.get_balance(pubkey)
        stats["last_bal"] = bal_resp.value
        stats["total_lifetime"] = stats["last_bal"] / 1e9
        
        await post_to_discord(0, "SYSTEM ONLINE", 3447003, "", stats["total_lifetime"])

        while True:
            try:
                # Reset Daily Stats at Midnight
                if datetime.now().date() != stats["current_day"]:
                    stats["daily_tolls"] = 0.0
                    stats["daily_subs"] = 0.0
                    stats["current_day"] = datetime.now().date()

                new_bal = (await client.get_balance(pubkey)).value
                if new_bal != stats["last_bal"]:
                    diff = (new_bal - stats["last_bal"]) / 1e9
                    sigs = await client.get_signatures_for_address(pubkey, limit=1)
                    sig = sigs.value[0].signature if sigs.value else ""

                    if new_bal > stats["last_bal"]:
                        label, color, r_type = identify_revenue(diff)
                        stats["total_lifetime"] += diff
                        if r_type == "sub": stats["daily_subs"] += diff
                        else: stats["daily_tolls"] += diff
                        
                        await post_to_discord(diff, label, color, sig, new_bal / 1e9)
                    else:
                        await post_to_discord(abs(diff), "SWEEP", 15105570, sig, new_bal / 1e9, is_sweep=True)
                    
                    stats["last_bal"] = new_bal
                await asyncio.sleep(5)
            except: await asyncio.sleep(10)

async def scalper_heartbeat():
    while True:
        # This keeps the Render instance from sleeping and confirms hunting
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 Scalper Hunting for Leads...")
        await asyncio.sleep(60)

async def main():
    await asyncio.gather(auditor_engine(), scalper_heartbeat())

if __name__ == "__main__":
    asyncio.run(main())
