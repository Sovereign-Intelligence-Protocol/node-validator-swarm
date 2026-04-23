import os, asyncio, httpx, sqlite3
from datetime import datetime
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

load_dotenv()
HOT_WALLET = os.getenv("HOT_WALLET_ADDRESS")
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

async def alert(amount, category, sig):
    stats, price = await get_stats_and_price()
    payload = {"embeds": [{"title": f"🚨 {category}", "color": 3066993, "fields": [
        {"name": "Amount", "value": f"`{amount:.4f} SOL` (~${amount*price:.2f})", "inline": True},
        {"name": "Vault Total", "value": f"`{stats['total_lifetime']:.4f} SOL`", "inline": True},
        {"name": "Proof", "value": f"[Solscan](https://solscan.io/tx/{sig})", "inline": False}
    ]}]}
    async with httpx.AsyncClient() as client: await client.post(DISCORD_WEBHOOK, json=payload)

async def auditor():
    init_db()
    async with AsyncClient(RPC_URL) as client:
        pk = Pubkey.from_string(HOT_WALLET)
        last_bal = (await client.get_balance(pk)).value
        print(f"🕵️ Auditor Live: {HOT_WALLET[:6]}...")
        while True:
            try:
                sigs = await client.get_signatures_for_address(pk, limit=5)
                if not sigs.value: continue
                for tx in reversed(sigs.value):
                    s_str = str(tx.signature)
                    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                    if not c.execute("SELECT 1 FROM processed_sigs WHERE sig=?", (s_str,)).fetchone():
                        await asyncio.sleep(2)
                        new_bal = (await client.get_balance(pk)).value
                        if new_bal > last_bal:
                            diff = (new_bal - last_bal) / 1e9
                            ctype = "sub" if diff > 1.0 else "toll"
                            c.execute("INSERT INTO processed_sigs VALUES (?)", (s_str,))
                            c.execute("UPDATE stats SET value = value + ? WHERE key = ?", (diff, "daily_"+ctype+"s"))
                            c.execute("UPDATE stats SET value = value + ? WHERE key = 'total_lifetime'", (diff,))
                            conn.commit()
                            await alert(diff, ctype.upper(), s_str)
                        last_bal = new_bal
                    conn.close()
                await asyncio.sleep(10)
            except Exception as e: print(f"Error: {e}"); await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(auditor())
