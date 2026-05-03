import os, asyncio, threading, base58, httpx
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

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
    """Hardened Telegram sender with logging."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("!!! TELEGRAM ERROR: Missing Token or Chat ID in Environment Variables !!!")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Added a 10s timeout to prevent hanging
            resp = await client.post(url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                print(f"Telegram Sent: {text[:20]}...")
            else:
                print(f"!!! TELEGRAM FAIL: {resp.status_code} - {resp.text}")
                print(f"Check if you have messaged your bot and if Chat ID {TG_CHAT_ID} is correct.")
        except Exception as e:
            print(f"!!! TELEGRAM CONNECTION ERROR: {e}")

async def check_arbitrage(amount_in_lamports):
    """Jupiter Price Check."""
    async with httpx.AsyncClient() as client:
        try:
            quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint={SOL_MINT}&outputMint={JITOSOL_MINT}&amount={amount_in_lamports}&slippageBps=1"
            resp = await client.get(quote_url, timeout=5.0)
            quote = resp.json()
            out_amount = int(quote.get('outAmount', 0))
            if out_amount > (amount_in_lamports * 1.001): 
                return True, quote
        except:
            pass
    return False, None

async def monitor_loop():
    # TEST MESSAGE: If you don't see this, the variables are wrong
    print("Attempting initial Telegram handshake...")
    await send_tg("🚀 *S.I.P. Omnicore Status:* Hardened Handshake Successful. Trading Engine Engaged.")
    
    trade_size = 100_000_000 # 0.1 SOL
    
    while True:
        try:
            is_profitable, quote = await check_arbitrage(trade_size)
            if is_profitable:
                profit = (int(quote['outAmount']) - trade_size) / 1e9
                await send_tg(f"💰 *PROFIT ALERT:* {profit:.6f} SOL arbitrage gap detected!")
            
            # Fast scan (every 10s)
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Monitor Loop Error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
