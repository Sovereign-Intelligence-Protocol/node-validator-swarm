import os
import asyncio
import httpx
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

# Load Environment Variables
load_dotenv()

# --- CONFIG ---
HOT_WALLET = os.getenv("HOT_WALLET_ADDRESS")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"
DB_PATH = "/var/data/protocol_vault.db"

# --- DATABASE SETUP ---
def init_db():
    try:
        print(f"📂 Verifying storage path: {os.path.dirname(DB_PATH)}")
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        print(f"🗄️ Connecting to vault at {DB_PATH}...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create tables for stats and duplicate prevention
        c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
        
        # Initialize default keys if the DB is brand new
        for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
            c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        raise

def get_db_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM stats")
    data = dict(c.fetchall())
    conn.close()
    return data

def record_tx(sig, amount, category_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Convert signature object to string for SQLite storage
        sig_str = str(sig)
        c.execute("INSERT INTO processed_sigs (sig) VALUES (?)", (sig_str,))
        
        stat_key = "daily_subs" if category_type == "sub" else "daily_tolls"
        c.execute("UPDATE stats SET value = value + ? WHERE key = ?", (amount, stat_key))
        c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (amount,))
        
        conn.commit()
        print(f"💾 Recorded {amount} SOL to vault. Type: {category_type}")
        return True
    except sqlite3.IntegrityError:
        return False # Already processed this signature
    finally:
        conn.close()

# --- REVENUE TRACKING ---
async def get_sol_price():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            return float(r.json()['price'])
    except:
        return 150.0 # Fallback price

async def post_audit_card(amount, category, color, sig, identity="New User"):
    data = get_db_stats()
    price = await get_sol_price()
    
    payload = {
        "embeds": [{
            "title": f"🚨 {category} DETECTED",
            "color": color,
            "fields": [
                {"name": "Contributor", "value": f"**{identity}**", "inline": False},
                {"name": "Amount", "value": f"`{amount:.6f} SOL` (~${amount*price:.2f})", "inline": True},
                {"name": "Vault Total", "value": f"**`{data['total_lifetime']:.4f} SOL` (~${data['total_lifetime']*price:,.2f})**", "inline": False},
                {"name": "System Status", "value": "🟢 SCALPING ACTIVE | 💾 DATA SECURED", "inline": True},
                {"name": "Audit Trail", "value": f"[View on Solscan](https://solscan.io/tx/{sig})", "inline": False}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

async def send_heartbeat(status_msg):
    data = get_db_stats()
    price = await get_sol_price()
    payload = {
        "embeds": [{
            "title": "🚨 SYSTEM ONLINE",
            "color": 3447003,
            "fields": [
                {"name": "Bridge Balance", "value": f"`{data['total_lifetime']:.4f} SOL`", "inline": True},
                {"name": "Daily Stats", "value": f"Tolls: {data['daily_tolls']:.2f} | Subs: {data['daily_subs']:.2f}", "inline": False},
                {"name": "System Status", "value": f"🟢 {status_msg}", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

# --- ENGINE CORES ---
async def auditor_loop():
    init_db()
    await send_heartbeat("SCALPING ACTIVE")
    
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        print(f"🕵️ Auditor Active for {HOT_WALLET}")
        
        # Get starting balance
        bal_resp = await client.get_balance(pubkey)
        last_check_bal = bal_resp.value
        
        while True:
            try:
                # Scan last 10 signatures
                sig_resp = await client.get_signatures_for_address(pubkey, limit=10)
                if not sig_resp.value: 
                    await asyncio.sleep(10)
                    continue

                for tx in reversed(sig_resp.value):
                    sig = tx.signature
                    
                    # Check if signature is already in DB
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (str(sig),))
                    exists = c.fetchone()
                    conn.close()
                    
                    if not exists:
                        # Wait a moment for balance to update on-chain
                        await asyncio.sleep(2)
                        new_bal_resp = await client.get_balance(pubkey)
                        new_bal = new_bal_resp.value
                        
                        if new_bal > last_check_bal:
                            diff = (new_bal - last_check_bal) / 1e9
                            cat = "💎 SUBSCRIPTION" if diff > 1.0 else "⛽ TRADE TOLL (1%)"
                            ctype = "sub" if diff > 1.0 else "toll"
                            
                            if record_tx(sig, diff, ctype):
                                await post_audit_card(diff, cat, 3066993, sig)
                        
                        last_check_bal = new_bal
                
                await asyncio.sleep(10) # Safety buffer to avoid RPC rate limits
            except Exception as e:
                print(f"⚠️ Auditor Loop Error: {e}")
                await asyncio.sleep(20)

async def scalper_engine():
    while True:
        print("🟢 Lead Scalper: Searching for profitable signals...")
        await asyncio.sleep(300) # Print every 5 minutes to keep logs clean

async def main():
    # Run both the tracker and the scalper logic simultaneously
    await asyncio.gather(auditor_loop(), scalper_engine())

if __name__ == "__main__":
    asyncio.run(main())
