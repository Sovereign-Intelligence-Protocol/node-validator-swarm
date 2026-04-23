import os
import asyncio
import httpx
import sqlite3
import base58
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

load_dotenv()

# --- CONFIG FROM YOUR RENDER ENVS ---
RPC_URL = os.getenv("HELIUS_RPC_URL") or os.getenv("RPC_URL") or "https://api.mainnet-beta.solana.com"
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
JITO_ENGINE = os.getenv("JITO_BLOCK_ENGINE_URL") # From your screenshot
DB_PATH = "/var/data/protocol_vault.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
    for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
        c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
    conn.commit(); conn.close()

async def get_stats_and_price():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
        c.execute("SELECT key, value FROM stats"); data = dict(c.fetchall()); conn.close()
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT", timeout=5)
            price = float(r.json()['price'])
    except:
        data = {'total_lifetime': 0.0, 'daily_tolls': 0.0, 'daily_subs': 0.0}
        price = 150.0
    return data, price

async def send_heartbeat(status_msg, current_bal):
    data, price = await get_stats_and_price()
    provider = "Helius + Jito" if JITO_ENGINE else "Public"
    
    payload = {
        "embeds": [{
            "title": "⚡ SOVEREIGN INTEL: LIVE",
            "color": 3066993,
            "fields": [
                {"name": "Seed Wallet", "value": f"`{current_bal:.4f} SOL`", "inline": True},
                {"name": "MEV Protection", "value": f"**{provider}**", "inline": True},
                {"name": "Total Recorded", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": False},
                {"name": "Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intelligence Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try: await client.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        except: print("⚠️ Discord Webhook Offline")

async def auditor():
    init_db()
    if not SEED_WALLET: return

    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        pk = Pubkey.from_string(SEED_WALLET)
        
        # Initial Force Sync with your OKX balance
        print(f"📡 Syncing with Seed: {SEED_WALLET[:6]}")
        res = await client.get_balance(pk)
        current_bal = res.value / 1e9
        
        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
        c.execute("UPDATE stats SET value = ? WHERE key = 'total_lifetime'", (current_bal,))
        conn.commit(); conn.close()
        
        await send_heartbeat("READY TO SNIPE", current_bal)

        last_bal = res.value
        while True:
            try:
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if sig_resp.value:
                    for tx in reversed(sig_resp.value):
                        s_str = str(tx.signature)
                        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
                        if not c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,)).fetchone():
                            await asyncio.sleep(1)
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
            except Exception as e:
                print(f"⚠️ Lag: {e}"); await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(auditor())
