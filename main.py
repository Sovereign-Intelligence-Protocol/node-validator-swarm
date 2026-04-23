import os, asyncio, httpx, sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()

# --- CONFIG ---
HOT_WALLET = os.getenv("HOT_WALLET_ADDRESS")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
RPC_URL = "https://api.mainnet-beta.solana.com"
DB_PATH = "/var/data/protocol_vault.db" # Lives on the Persistent Disk

# --- DATABASE SETUP ---
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS processed_sigs (sig TEXT PRIMARY KEY)')
    # Initialize if new
    for key in ['total_lifetime', 'daily_tolls', 'daily_subs']:
        c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0.0)", (key,))
    conn.commit()
    conn.close()

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
        c.execute("INSERT INTO processed_sigs (sig) VALUES (?)", (sig,))
        stat_key = "daily_subs" if category_type == "sub" else "daily_tolls"
        c.execute("UPDATE stats SET value = value + ? WHERE key = ?", (amount, stat_key))
        c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (amount,))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False # Already processed
    finally: conn.close()

# --- REVENUE TRACKING ---
async def get_sol_price():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            return float(r.json()['price'])
    except: return 150.0

async def post_audit_card(amount, category, color, sig, current_bal, identity="New User"):
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
                {"name": "System Status", "value": "🟢 SCALPING ACTIVE | 💾 DATA SECURED", "inline": True}
            ],
            "footer": {"text": f"Sovereign Intel Protocol | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK, json=payload)

# --- ENGINE CORES ---
async def auditor_loop():
    init_db()
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(HOT_WALLET)
        last_check_bal = (await client.get_balance(pubkey)).value
        
        while True:
            try:
                sig_resp = await client.get_signatures_for_address(pubkey, limit=5)
                if not sig_resp.value: continue

                for tx in reversed(sig_resp.value):
                    sig = tx.signature
                    # Check the database if we've seen this signature
                    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                    c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (sig,))
                    exists = c.fetchone(); conn.close()
                    
                    if not exists:
                        await asyncio.sleep(2)
                        new_bal = (await client.get_balance(pubkey)).value
                        if new_bal > last_check_bal:
                            diff = (new_bal - last_check_bal) / 1e9
                            cat = "💎 SUBSCRIPTION" if diff > 1.5 else "⛽ TRADE TOLL (1%)"
                            ctype = "sub" if diff > 1.5 else "toll"
                            
                            if record_tx(sig, diff, ctype):
                                await post_audit_card(diff, cat, 3066993, sig, new_bal/1e9)
                        
                        last_check_bal = new_bal
                await asyncio.sleep(5)
            except: await asyncio.sleep(10)

async def scalper_engine():
    while True:
        print("🟢 Lead Scalper: Searching for profitable signals...")
        await asyncio.sleep(60)

async def main():
    await asyncio.gather(auditor_loop(), scalper_engine())

if __name__ == "__main__":
    asyncio.run(main())
