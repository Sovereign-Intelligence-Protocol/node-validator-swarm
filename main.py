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
    "processed_sigs": set()  # Keeps us from double-reporting
}

async def get_sol_price():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            return float(resp.json()['price'])
    except: return 145.0 

def categorize(amount):
    if 1.9 <= amount <= 2.1: return "💎 API SUBSCRIPTION", 3447003, "sub"
    if 4.9 <= amount <= 5.1: return "🐋 WHALE PASS", 10181035, "sub"
    return "⛽ MICRO-TOLL (1%)", 3066993, "toll"

async def post_to_discord(amount, category, color, sig, current_bal):
    sol_price = await get_sol_price()
    usd = amount * sol_price
    
    payload = {
        "embeds": [{
            "title": f"📥 {category} DETECTED",
            "color": color,
            "fields": [
                {"name": "Amount", "value": f"`{amount:.6f} SOL` (~${usd:.4f})", "inline": True},
                {"name": "New Wallet Total", "value": f"`{current_bal:.4f} SOL`", "inline": True},
                {"name": "Status", "value": "🟢 SCALPING ACTIVE", "inline": False},
                {"name": "Verification", "value": f"[View Transaction on Solscan](https://solscan.io/tx/{sig})", "inline": False}
            ],
            "footer": {"text": f"Sovereign Intel Auditor | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def transaction_sniffer():
    global stats
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        print(f"🕵️ Auditor Sniffer Active on {HOT_WALLET}")

        # Initial balance sync
        start_bal = (await client.get_balance(pubkey)).value / 1e9
        stats["total_lifetime"] = start_bal

        while True:
            try:
                # Fetch the last 5 transactions (to catch rapid tolls)
                response = await client.get_signatures_for_address(pubkey, limit=5)
                if not response.value: continue

                for tx in reversed(response.value):
                    sig = tx.signature
                    if sig not in stats["processed_sigs"]:
                        # Get the transaction details to see exactly how much moved
                        tx_detail = await client.get_transaction(sig, max_supported_transaction_version=0)
                        
                        # Calculate the net change for our wallet in this specific TX
                        # Note: This is simplified; in a production toll-bridge, we look for 'postBalances'
                        curr_bal = (await client.get_balance(pubkey)).value / 1e9
                        diff = curr_bal - stats["total_lifetime"]

                        if diff > 0.000001:  # Only report if it's a real incoming toll
                            label, color, r_type = categorize(diff)
                            if r_type == "sub": stats["daily_subs"] += diff
                            else: stats["daily_tolls"] += diff
                            
                            stats["total_lifetime"] = curr_bal
                            await post_to_discord(diff, label, color, sig, curr_bal)
                        
                        stats["processed_sigs"].add(sig)
                        # Keep memory clean
                        if len(stats["processed_sigs"]) > 100: stats["processed_sigs"].pop()

                await asyncio.sleep(3) # Aggressive polling to catch every toll
            except Exception as e:
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(transaction_sniffer())
