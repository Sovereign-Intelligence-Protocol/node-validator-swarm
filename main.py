import os
import asyncio
import httpx
import sqlite3
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
DB_PATH = "protocol_vault.db" 

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
    # Fallback data if API hangs
    data = {'total_lifetime': 0.0, 'daily_tolls': 0.0, 'daily_subs': 0.0}
    price = 145.0 
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute("SELECT key, value FROM stats")
        data = dict(c.fetchall())
        conn.close()
        
        # Fixed: Added a 3-second timeout to prevent Binance from hanging the bot
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT")
            if r.status_code == 200:
                price = float(r.json()['price'])
    except Exception as e:
        print(f"⚠️ Price/DB Fetch bypassed: {e}")
