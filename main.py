import os, asyncio, threading, base58, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# --- RENDER HEARTBEAT ---
app = Flask(__name__)
@app.route('/')
def health(): return "OMNICORE: TRADING ACTIVE", 200
def run_heartbeat():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_heartbeat, daemon=True).start()

# --- CONFIG ---
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"
SOL_MINT = "So11111111111111111111111111111111111111112"

async def send_tg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": TG_CHAT_ID, "text": text})

async def check_arbitrage(amount_in_lamports):
    """Checks Jupiter for a profitable JitoSOL <-> SOL swap."""
    async with httpx.AsyncClient() as client:
        # Route: SOL to JitoSOL
        quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint={SOL_MINT}&outputMint={JITOSOL_MINT}&amount={amount_in_lamports}&slippageBps=1"
        resp = await client.get(quote_url)
        quote = resp.json()
        
        out_amount = int(quote.get('outAmount', 0))
        # Logic: If outAmount > inAmount (plus a small buffer for fees), we found a gap
        if out_amount > amount_in_lamports * 1.001: # 0.1% profit threshold
            return True, quote
    return False, None

async def monitor_loop():
    await send_tg("🚀 S.I.P. Omnicore: Trading Engine Engaged.")
    
    # We use 0.1 SOL as a test trade size
    trade_size = 100_000_000 
    
    while True:
        try:
            is_profitable, quote = await check_arbitrage(trade_size)
            
            if is_profitable:
                # In a full 'unrestricted' mode, we would execute the swap here.
                # For now, we alert your Telegram so you can see the 'Money' found.
                profit = (int(quote['outAmount']) - trade_size) / 1e9
                await send_tg(f"💰 PROFIT FOUND: {profit:.6f} SOL gap detected on JitoSOL pair!")
            
            # Scan every 10 seconds (Render can handle this easily)
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Engine Error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
