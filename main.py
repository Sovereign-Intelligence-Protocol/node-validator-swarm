import os
import asyncio
import httpx
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

# Load all variables from Render's Environment tab
load_dotenv()

# --- DYNAMIC CONFIGURATION ---
# This ensures we find your Helius RPC even if the name varies slightly
RPC_URL = (
    os.getenv("HELIUS_RPC_URL") or 
    os.getenv("SOLANA_RPC_URL") or 
    os.getenv("RPC_URL") or 
    "https://api.mainnet-beta.solana.com"
)
JITO_ENGINE = os.getenv("JITO_BLOCK_ENGINE_URL")
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DB_PATH = "/var/data/protocol_vault.db"

# --- DATABASE SETUP ---
def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
        for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
            c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Database Init Failed: {e}")

async def get_stats_and_price():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
        c.execute("SELECT key, value FROM stats"); data = dict(c.fetchall()); conn.close()
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT", timeout=5)
            price = float(r.json()['price'])
    except:
        data = {'total_lifetime': 0.0, 'daily_tolls': 0.0, 'daily_subs': 0.0}
        price = 145.0 # Fallback
    return data, price

# --- MESSAGING ENGINE ---
async def send_heartbeat(status_msg, current_bal):
    data, price = await get_stats_and_price()
    
    # Confirm bridge status for the Discord UI
    using_helius = "helius" in RPC_URL.lower()
    bridge_label = "Helius + Jito (Fast) ⚡" if using_helius and JITO_ENGINE else "Public (Slow) 🐌"
    
    payload = {
        "embeds": [{
            "title": "⚡ SOVEREIGN INTEL PROTOCOL v4.2",
            "color": 3066993,
            "fields": [
                {"name": "Seed Wallet (OKX)", "value": f"`{current_bal:.4f} SOL` (~${current_bal*price:.2f})", "inline": True},
                {"name": "Network Bridge", "value": f"**{bridge_label}**", "inline": True},
                {"name": "Wealth Generated", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": False},
                {"name": "System Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intelligence | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try: await client.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        except: print("⚠️ Discord Webhook unreachable")

# --- MAIN AUDIT ENGINE ---
async def auditor():
    init_db()
    if not SEED_WALLET:
        print("❌ FATAL: HOT_WALLET_ADDRESS not found in Render Envs!")
        return

    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        pk = Pubkey.from_string(SEED_WALLET)
        
        # Initial Balance Sync to clear the 0.0000 SOL bug
        print(f"📡 Syncing with Seed Wallet: {SEED_WALLET[:6]}...")
        try:
            res = await client.get_balance(pk)
            current_bal_sol = res.value / 1e9
            await send_heartbeat("ENGINE START: MONITORING ACTIVE", current_bal_sol)
            last_bal = res.value
        except Exception as e:
            print(f"⚠️ RPC Exception during sync: {e}")
            last_bal = 0

        while True:
            try:
                # Check for new transaction signatures
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if sig_resp.value:
                    for tx in reversed(sig_resp.value):
                        s_str = str(tx.signature)
                        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
                        c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,))
                        
                        if not c.fetchone():
                            # New activity detected!
                            await asyncio.sleep(2) # Buffer for balance update
                            new_res = await client.get_balance(pk)
                            new_bal = new_res.value
                            
                            if new_bal > last_bal:
                                # This is actual wealth/toll creation
                                diff = (new_bal - last_bal) / 1e9
                                c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                                c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                                conn.commit()
                                print(f"💰 Wealth Created: {diff} SOL")
                            
                            last_bal = new_bal
                        conn.close()
                
                await asyncio.sleep(5) # High-speed cycle
            except Exception as e:
                print(f"⚠️ Cycle Lag: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    print("🚀 Initializing Sovereign Protocol...")
    asyncio.run(auditor())
