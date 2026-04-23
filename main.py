import os
import asyncio
import httpx
import sqlite3
import sys
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

# Load variables from Render Dashboard
load_dotenv()

# --- CONFIGURATION ---
RPC_URL = (
    os.getenv("HELIUS_RPC_URL") or 
    os.getenv("SOLANA_RPC_URL") or 
    "https://api.mainnet-beta.solana.com"
)
JITO_ENGINE = os.getenv("JITO_BLOCK_ENGINE_URL")
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
# Use current working directory explicitly for Render
DB_PATH = os.path.join(os.getcwd(), "protocol_vault.db") 

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
        for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
            c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
        conn.commit()
        conn.close()
        print("✅ Audit 1: Database persistence confirmed.")
    except Exception as e:
        print(f"❌ DB Error: {e}")
        sys.exit(1) # Exit with error so Render logs it

async def get_stats_and_price():
    data = {'total_lifetime': 0.0, 'daily_tolls': 0.0, 'daily_subs': 0.0}
    price = 145.0 
    try:
        conn = sqlite3.connect(DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute("SELECT key, value FROM stats")
        rows = dict(c.fetchall())
        if rows: data.update(rows)
        conn.close()
        
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            if r.status_code == 200:
                price = float(r.json()['price'])
    except Exception:
        pass # Silence price errors to keep heartbeat alive
    return data, price

async def send_heartbeat(status_msg, current_bal):
    data, price = await get_stats_and_price()
    is_helius = "helius" in RPC_URL.lower()
    bridge_label = "Helius + Jito ⚡" if is_helius and JITO_ENGINE else "Public Bridge 🐌"
    
    payload = {
        "embeds": [{
            "title": "⚡ SOVEREIGN PROTOCOL: ACTIVE",
            "color": 3066993,
            "fields": [
                {"name": "Seed Wallet (Kraken)", "value": f"`{current_bal:.4f} SOL`", "inline": True},
                {"name": "Network Bridge", "value": f"**{bridge_label}**", "inline": True},
                {"name": "Total Wealth", "value": f"`{data.get('total_lifetime', 0):.4f} SOL`", "inline": False},
                {"name": "System Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Audit Cycle Live | {datetime.now().strftime('%H:%M:%S')} UTC"}
        }]
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            await client.post(DISCORD_WEBHOOK, json=payload)
        except Exception:
            print("⚠️ Audit 2: Discord Webhook timed out - retrying next cycle.")

async def auditor():
    init_db()
    if not SEED_WALLET or not DISCORD_WEBHOOK:
        print("❌ CRITICAL: Missing Environment Variables!")
        sys.exit(1)

    print(f"🚀 ENGINE START: Monitoring {SEED_WALLET}")
    
    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        try:
            pk = Pubkey.from_string(SEED_WALLET)
            res = await client.get_balance(pk)
            last_bal = res.value
            await send_heartbeat("ENGINE INITIALIZED", last_bal / 1e9)
        except Exception as e:
            print(f"⚠️ Initial connection failed: {e}")
            last_bal = 0

        while True:
            try:
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if sig_resp and sig_resp.value:
                    for tx in reversed(sig_resp.value):
                        s_str = str(tx.signature)
                        conn = sqlite3.connect(DB_PATH, timeout=20)
                        c = conn.cursor()
                        if not c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,)).fetchone():
                            await asyncio.sleep(2)
                            new_res = await client.get_balance(pk)
                            new_bal = new_res.value
                            if new_bal > last_bal:
                                diff = (new_bal - last_bal) / 1e9
                                c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                                c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                                conn.commit()
                                await send_heartbeat("REVENUE DETECTED 💰", new_bal / 1e9)
                            last_bal = new_bal
                        conn.close()
                await asyncio.sleep(20) # Conservative timing to stay under RPC limits
            except Exception as e:
                print(f"⚠️ RPC Loop: {e}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(auditor())
    except KeyboardInterrupt:
        print("🛑 System manual shutdown.")
