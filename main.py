import os
import asyncio
import httpx
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

# Load Environment Variables from Render
load_dotenv()

# --- CONFIGURATION (Mapped to your Render Envs) ---
# This prioritized your Helius and Jito keys for the "Fast Lane"
RPC_URL = os.getenv("HELIUS_RPC_URL") or os.getenv("SOLANA_RPC_URL") or "https://api.mainnet-beta.solana.com"
JITO_ENGINE = os.getenv("JITO_BLOCK_ENGINE_URL")
SEED_WALLET = os.getenv("HOT_WALLET_ADDRESS") 
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DB_PATH = "/var/data/protocol_vault.db"

# --- DATABASE ENGINE ---
def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        # timeout=10 prevents the bot from crashing on Render's network storage
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
        # Ensure counters exist
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
        price = 150.0
    return data, price

# --- NOTIFICATION SYSTEM ---
async def send_heartbeat(status_msg, current_bal):
    data, price = await get_stats_and_price()
    
    # Identify the bridge type for the Discord card
    is_helius = "helius" in RPC_URL.lower()
    network_label = "Helius + Jito (Fast Lane) ⚡" if is_helius and JITO_ENGINE else "Public (Congested) 🐌"
    
    payload = {
        "embeds": [{
            "title": "⚡ SOVEREIGN INTEL PROTOCOL",
            "color": 3066993,
            "fields": [
                {"name": "Seed Wallet (OKX)", "value": f"`{current_bal:.4f} SOL` (~${current_bal*price:.2f})", "inline": True},
                {"name": "Network Bridge", "value": f"**{network_label}**", "inline": True},
                {"name": "Wealth Created", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": False},
                {"name": "System Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Audit Cycle Active | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        try: await client.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        except: print("⚠️ Webhook Failed")

# --- AUDIT ENGINE ---
async def auditor():
    init_db()
    if not SEED_WALLET or not DISCORD_WEBHOOK:
        print("❌ FATAL: Missing Environment Variables in Render!")
        return

    async with AsyncClient(RPC_URL, commitment=Processed) as client:
        pk = Pubkey.from_string(SEED_WALLET)
        
        # FORCED INITIAL SYNC: This fixes the 0.0000 SOL display
        print(f"📡 Syncing with Blockchain: {SEED_WALLET[:6]}...")
        res = await client.get_balance(pk)
        current_bal_sol = res.value / 1e9
        
        # We start tracking wealth from this point forward
        await send_heartbeat("SNIPER INITIALIZED", current_bal_sol)

        last_bal = res.value
        while True:
            try:
                # Polling recent transactions
                sig_resp = await client.get_signatures_for_address(pk, limit=5)
                if sig_resp.value:
                    for tx in reversed(sig_resp.value):
                        s_str = str(tx.signature)
                        conn = sqlite3.connect(DB_PATH, timeout=10); c = conn.cursor()
                        c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,))
                        
                        if not c.fetchone():
                            # New transaction detected
                            await asyncio.sleep(1.5) # Wait for balance to settle
                            new_res = await client.get_balance(pk)
                            new_bal = new_res.value
                            
                            if new_bal > last_bal:
                                # New revenue detected!
                                diff = (new_bal - last_bal) / 1e9
                                c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                                c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                                conn.commit()
                                print(f"💰 Revenue Detected: {diff} SOL")
                            
                            last_bal = new_bal
                        conn.close()
                
                # High-frequency check (5 seconds) for sniper agility
                await asyncio.sleep(5)
            except Exception as e:
                print(f"⚠️ RPC Lag: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    print("🚀 Protocol Launching...")
    asyncio.run(auditor())
