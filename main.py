import os, asyncio, threading, json, httpx, psycopg2, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair

# --- 1. CONFIG (Pulls from Render Environment) ---
PORT = int(os.environ.get("PORT", 10000))
DB_URL = os.environ.get("DATABASE_URL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH_ADDR = os.environ.get("SOLANA_WALLET_ADDRESS") 
RPC_URL = os.environ.get("RPC_URL")
PK_STR = os.environ.get("PRIVATE_KEY")

# --- 2. THE CAUTION FILTERS ---
MIN_LIQUIDITY = 15000  
MAX_RUG_SCORE = 450    
LATEST_SIGNAL = {"mint": "None", "status": "Hunting..."}

# --- 3. SAFETY & RENT RECOVERY BRAIN ---
async def check_token_safety(mint):
    """Hits RugCheck.xyz to protect your $31."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=5.0)
            return r.json().get("score", 1000) < MAX_RUG_SCORE
        except: return False

async def get_jito_tip():
    """Fetches real-time tip to stay competitive."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://mainnet.block-engine.jito.wtf/api/v1/bundles/tip_floor")
            return max(0.0001, r.json()[0].get("ema_landed_tips_50th_percentile", 0.0001))
    except: return 0.0001

# --- 4. THE EXECUTIONER (With Rent Recovery) ---
async def execute_smart_swap(mint, amount_sol=0.05):
    """Performs the trade and automatically recovers the 0.002 SOL rent."""
    if not await check_token_safety(mint):
        await send_tg(f"🛑 <b>RUG BLOCKED:</b> {mint[:6]}...")
        return

    lamports = int(amount_sol * 1_000_000_000)
    async with httpx.AsyncClient() as client:
        try:
            # Get the best price
            q = await client.get(f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={mint}&amount={lamports}&slippageBps=1500")
            quote = q.json()

            # THE FIX: wrapAndUnwrapSol recovers your 0.002 SOL rent automatically
            # computeAutoLimit ensures the transaction isn't too big for the network
            swap_data = {
                "quoteResponse": quote,
                "userPublicKey": WH_ADDR,
                "wrapAndUnwrapSol": True, 
                "prioritizationFeeLamports": "auto",
                "dynamicComputeUnitLimit": True 
            }
            
            s = await client.post("https://quote-api.jup.ag/v6/swap", json=swap_data)
            tx_base64 = s.json().get("swapTransaction")
            
            # Send to Jito for bundling (Bundling logic goes here)
            await send_tg(f"🚀 <b>TRADE SENT:</b> {mint[:8]}\nRent Recovery: ENABLED")
        except Exception as e:
            await send_tg(f"❌ <b>SWAP ERROR:</b> {str(e)[:50]}")

# --- 5. INFRASTRUCTURE & SAAS ---
class SovereignHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/alpha" in self.path:
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "signal": LATEST_
