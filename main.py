import os
import asyncio
import httpx
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- CONFIG ---
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS") # This is your junT...tWs address
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"
DB_PATH = "/var/data/protocol_vault.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
    for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
        c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
    conn.commit()
    conn.close()

async def get_stats_and_price():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT key, value FROM stats"); data = dict(c.fetchall()); conn.close()
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            price = float(r.json()['price'])
    except: price = 150.0
    return data, price

async def send_heartbeat(status_msg, seed_bal):
    data, price = await get_stats_and_price()
    payload = {
        "embeds": [{
            "title": "🚀 SNIPER SEED ACTIVE",
            "color": 15105570, # Orange for "Ready to Fire"
            "fields": [
                {"name": "Seed Balance", "value": f"`{seed_bal:.4f} SOL`", "inline": True},
                {"name": "Status", "value": f"🟢 {status_msg}", "inline": True},
                {"name": "Vault Total", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": False}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def auditor():
    init_db()
    async with AsyncClient(RPC_URL) as client:
        pk = Pubkey.from_string(SEED_WALLET)
        
        # Initial Seed Sync
        print(f"📡 Syncing Seed Wallet: {SEED_WALLET}")
        res = await client.get_balance(pk)
        current_bal = res.value / 1e9
        
        # Update DB with current seed state
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("UPDATE stats SET value = ? WHERE key = 'total_lifetime'", (current_bal,))
        conn.commit(); conn.close()
        
        await send_heartbeat("SNIPER READY", current_bal)

        last_bal = res.value
        while True:
            try:
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if sig_resp.value:
                    for tx in reversed(sig_resp.value):
                        s_str = str(tx.signature)
                        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                        if not c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,)).fetchone():
                            await asyncio.sleep(2)
                            new_res = await client.get_balance(pk)
                            new_bal = new_res.value
                            if new_bal > last_bal:
                                diff = (new_bal - last_bal) / 1e9
                                c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                                c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                                conn.commit()
                            last_bal = new_bal
                        conn.close()
                await asyncio.sleep(10)
            except Exception as e:
                print(f"Error: {e}"); await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(auditor())
