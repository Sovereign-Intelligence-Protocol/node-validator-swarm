import os, asyncio, json, httpx, base58
from dotenv import load_dotenv
from solders.keypair import Keypair as SoldersKeypair

load_dotenv()

# --- CONFIG ---
KRAKEN_DEST = os.getenv("KRAKEN_DESTINATION") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
# Using a reliable public RPC for balance checks
RPC_URL = "https://api.mainnet-beta.solana.com"

async def get_sol_balance(addr):
    try:
        async with httpx.AsyncClient() as client:
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [addr]}
            r = await client.post(RPC_URL, json=payload, timeout=10.0)
            return r.json()['result']['value'] / 1e9
    except Exception as e:
        print(f"Balance Check Error: {e}")
        return 0.0

async def force_discord_report():
    if not DISCORD_WEBHOOK or not KRAKEN_DEST:
        print("MISSING CONFIG: Check DISCORD_WEBHOOK_URL and KRAKEN_DESTINATION in Render.")
        return
    
    current_val = await get_sol_balance(KRAKEN_DEST)
    
    # This payload is designed to be UNSTOPPABLE. 
    # It sends both a raw text 'content' AND a fancy 'embed'.
    payload = {
        "content": f"📈 **TREASURY UPDATE:** {current_val:.4f} SOL currently in Kraken Vault.",
        "embeds": [{
            "title": "💰 REVENUE FLOW: ACTIVE",
            "color": 3066993, # Financial Green
            "fields": [
                {"name": "Vault Balance", "value": f"`{current_val:.4f} SOL`", "inline": True},
                {"name": "Wallet", "value": f"`{KRAKEN_DEST[:4]}...{KRAKEN_DEST[-4:]}`", "inline": True},
                {"name": "Bridge Status", "value": "✅ COLLECTING", "inline": False}
            ],
            "footer": {"text": "Sovereign Intelligence Protocol | Revenue Monitor"}
        }]
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(DISCORD_WEBHOOK, json=payload, timeout=10.0)
            print(f"Discord Response: {resp.status_code}")
        except Exception as e:
            print(f"Discord POST Error: {e}")

async def main():
    print("--- 2026 OMEGA REVENUE MONITOR STARTING ---")
    
    # 1. Immediate Report on Boot
    await force_discord_report()
    
    # 2. Continuous Loop
    while True:
        # Pings Discord every 15 minutes with the latest balance
        await asyncio.sleep(900) 
        await force_discord_report()

if __name__ == "__main__":
    asyncio.run(main())
