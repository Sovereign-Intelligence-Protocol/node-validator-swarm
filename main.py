import os
import asyncio
import httpx
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

# Load all Render Environment Variables
load_dotenv()

# --- CONFIGURATION (Mapped to your Dashboard) ---
# Hunts for Helius first to stay in the "Fast Lane"
RPC_URL = (
    os.getenv("HELIUS_RPC_URL") or 
    os.getenv("SOLANA_RPC_URL") or 
    "https://api.mainnet-beta.solana.com"
)
JITO_ENGINE = os.getenv("JITO_BLOCK_ENGINE_URL")
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DB_PATH = "protocol_vault.db" # Local root for Render stability

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
        for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
            c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ DB Error: {e}")

async def get_stats_and_price():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
        c.execute("SELECT key, value FROM stats"); data = dict(c.fetchall()); conn.close()
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT", timeout=5)
            price = float(r.json()['price'])
    except:
        data = {'total_lifetime': 0.0, 'daily_tolls': 0.0, 'daily_subs': 0.0}
        price = 145.0
    return data, price

async def send_heartbeat(status_msg, current_bal):
    data, price = await get_stats_and_price()
    
    # Logic to confirm Helius vs Public for the Discord label
    is_helius = "helius" in RPC_URL.lower()
    bridge_label = "Helius + Jito (Fast Lane) ⚡" if is_helius and JITO_ENGINE else "Public (Congested) 🐌"
    
    payload = {
        "embeds": [{
            "title": "⚡ SOVEREIGN PROTOCOL: PERFECTED",
            "color": 3066993,
            "fields": [
                {"name": "Seed Wallet (OKX)", "value": f"`{current_bal:.4f} SOL` (~${current_bal*price:.2f})", "inline": True},
                {"name": "Network Bridge", "value": f"**{bridge_label}**", "inline": True},
                {"name": "Wealth Created", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": False},
                {"name": "System Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Audit Cycle Live | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try: await client.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        except: pass

async def auditor():
    init_db()
    if not SEED_WALLET:
        print("❌ ERROR: HOT_WALLET_ADDRESS not found!")
        return

    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        pk = Pubkey.from_string(SEED_WALLET)
        
        # Immediate Balance Sync to recognize your 0.3649 SOL
        try:
            res = await client.get_balance(pk)
            current_bal_sol = res.value / 1e9
            await send_heartbeat("ENGINE ACTIVE", current_bal_sol)
            last_bal = res.value
        except:
            last_bal = 0

        while True:
            try:
                # Scans last 5 signatures for new wealth/tolls
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if sig_resp and sig_resp.value:
                    for tx in reversed(sig_resp.value):
                        s_str = str(tx.signature)
                        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
                        if not c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,)).fetchone():
                            await asyncio.sleep(2) # Buffer for chain sync
                            new_res = await client.get_balance(pk)
                            new_bal = new_res.value
                            
                            if new_bal > last_bal:
                                diff = (new_bal - last_bal) / 1e9
                                c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                                c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                                conn.commit()
                            last_bal = new_bal
                        conn.close()
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(10) # Auto-retry on RPC exceptions

if __name__ == "__main__":
    asyncio.run(auditor())
