import os
import asyncio
import httpx
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

# Load Environment Variables from Render
load_dotenv()

# --- CONFIG ---
HOT_WALLET = os.getenv("HOT_WALLET_ADDRESS")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"
DB_PATH = "/var/data/protocol_vault.db"

# --- DATABASE SETUP ---
def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
        # Initialize keys if they don't exist
        for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
            c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
        conn.commit()
        conn.close()
        print(f"✅ Vault connected at {DB_PATH}")
    except Exception as e:
        print(f"❌ DB Initialization Error: {e}")

async def get_stats_and_price():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM stats")
    data = dict(c.fetchall())
    conn.close()
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            price = float(r.json()['price'])
    except:
        price = 150.0 # Fallback
    return data, price

# --- DISCORD REPORTING ---
async def send_heartbeat(status_msg):
    data, price = await get_stats_and_price()
    # Pull fresh balance for the card
    async with AsyncClient(RPC_URL) as client:
        pk = Pubkey.from_string(HOT_WALLET)
        res = await client.get_balance(pk)
        live_bal = res.value / 1e9

    payload = {
        "embeds": [{
            "title": "🚨 SYSTEM ONLINE",
            "color": 3447003,
            "fields": [
                {"name": "Live Bridge Balance", "value": f"`{live_bal:.4f} SOL` (~${live_bal*price:.2f})", "inline": True},
                {"name": "Total Wealth Recorded", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": True},
                {"name": "Daily Stats", "value": f"Tolls: {data['daily_tolls']:.2f} | Subs: {data['daily_subs']:.2f}", "inline": False},
                {"name": "System Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def alert_revenue(amount, category, sig):
    _, price = await get_stats_and_price()
    payload = {
        "embeds": [{
            "title": f"🚨 {category} DETECTED",
            "color": 3066993,
            "fields": [
                {"name": "Amount", "value": f"`{amount:.4f} SOL` (~${amount*price:.2f})", "inline": True},
                {"name": "Proof", "value": f"[View on Solscan](https://solscan.io/tx/{sig})", "inline": False}
            ]
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

# --- THE AUDITOR (MONEY TRACKER) ---
async def auditor():
    init_db()
    if not HOT_WALLET or not DISCORD_WEBHOOK:
        print("❌ ERROR: Missing Environment Variables!")
        return

    async with AsyncClient(RPC_URL) as client:
        pk = Pubkey.from_string(HOT_WALLET)
        
        # Initial Blockchain Sync
        print(f"📡 Syncing with wallet: {HOT_WALLET}")
        bal_resp = await client.get_balance(pk)
        last_bal = bal_resp.value
        
        # Update DB with current wallet state immediately
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("UPDATE stats SET value = ? WHERE key = 'total_lifetime'", (last_bal / 1e9,))
        conn.commit(); conn.close()
        
        await send_heartbeat("SCALPING ACTIVE")

        while True:
            try:
                # Check for new transactions
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if not sig_resp.value:
                    await asyncio.sleep(10)
                    continue

                for tx in reversed(sig_resp.value):
                    s_str = str(tx.signature)
                    
                    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                    c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,))
                    if not c.fetchone():
                        # New transaction found! Wait for balance to settle
                        await asyncio.sleep(2)
                        new_bal_resp = await client.get_balance(pk)
                        new_bal = new_bal_resp.value
                        
                        if new_bal > last_bal:
                            diff = (new_bal - last_bal) / 1e9
                            ctype = "SUBSCRIPTION" if diff > 1.0 else "TRADE TOLL"
                            # Record it
                            c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                            stat_key = "daily_subs" if diff > 1.0 else "daily_tolls"
                            c.execute("UPDATE stats SET value = value + ? WHERE key = ?", (diff, stat_key))
                            c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                            conn.commit()
                            await alert_revenue(diff, ctype, s_str)
                        
                        last_bal = new_bal
                    conn.close()
                
                await asyncio.sleep(10)
            except Exception as e:
                print(f"⚠️ Loop Error: {e}")
                await asyncio.sleep(20)

if __name__ == "__main__":
    print("🚀 Protocol Starting...")
    asyncio.run(auditor())
