import os, asyncio, httpx, threading, time, base64, psycopg2
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIG (Mapped to Render Dashboard) ---
PORT = int(os.getenv("PORT", 10000))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = str(os.getenv("TELEGRAM_ADMIN_ID", "")).strip()
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
WALLET_ADDR = os.getenv("WALLET_ADDRESS")
PRIV_KEY_STR = os.getenv("PRIVATE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

running = True

def get_keypair():
    try:
        if not PRIV_KEY_STR: return None
        if PRIV_KEY_STR.startswith("["): return Keypair.from_json(PRIV_KEY_STR)
        return Keypair.from_base58_string(PRIV_KEY_STR)
    except: return None

async def send_tg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": ADMIN_ID, "text": f"🦅 PREDATOR:\n{msg}"})
    except: pass

def log_trade(tx_sig, amount, status):
    if not DATABASE_URL: return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO trades (signature, amount, status, timestamp) VALUES (%s, %s, %s, NOW())", (tx_sig, amount, status))
        conn.commit()
        cur.close(); conn.close()
    except: pass

async def fire_swap(target_mint, amount_sol=0.01):
    kp = get_keypair()
    if not kp: return "❌ KEY ERROR"
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            # Jupiter Quote
            q_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={target_mint}&amount={int(amount_sol * 10**9)}&dynamicSlippage=true&maxSlippageBps=200"
            quote = (await client.get(q_url)).json()
            
            # Swap Build
            s_res = await client.post("https://quote-api.jup.ag/v6/swap", json={
                "quoteResponse": quote,
                "userPublicKey": str(kp.pubkey()),
                "wrapAndUnwrapSol": True,
                "prioritizationFeeLamports": "auto"
            })
            tx_data = s_res.json().get("swapTransaction")
            
            # Sign & Jito MEV-Safe Broadcast
            raw_tx = VersionedTransaction.from_bytes(base64.b64decode(tx_data))
            signature = kp.sign_message(raw_tx.message.to_bytes_versioned())
            signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
            
            payload = {
                "jsonrpc": "2.0", "id": 1, "method": "sendTransaction",
                "params": [base64.b64encode(bytes(signed_tx)).decode('utf-8'), {"encoding": "base64"}]
            }
            final = await client.post("https://mainnet.block-engine.jito.wtf/api/v1/transactions", json=payload)
            res = final.json().get("result")
            
            if res:
                log_trade(res, amount_sol, "SUCCESS")
                return f"🎯 KILL CONFIRMED: https://solscan.io/tx/{res}"
            return "⚠️ Jito Bundle Rejected"
    except Exception as e: return f"❌ ERROR: {str(e)}"

async def predator_scanner():
    await send_tg("👁️ GOD MODE v16.2.3 LIVE.\nHeartbeat: 120s Pulse Active.\nShield: MEV-Jito Active.")
    while running:
        try:
            # Pulse logic for Render stability
            print(f"Pulse check: {time.ctime()} - Standing by.")
            
            target = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            sig = await fire_swap(target, 0.01)
            if "🎯" in sig:
                await send_tg(sig)
                # break  # Uncomment to stop after one successful test
        except: pass
        await asyncio.sleep(120) 

async def command_listener():
    last_id = 0
    async with httpx.AsyncClient() as client:
        while running:
            try:
                r = await client.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}&timeout=10")
                for update in r.json().get("result", []):
                    last_id = update["update_id"]
                    msg = update.get("message", {})
                    if str(msg.get("from", {}).get("id")) == ADMIN_ID:
                        if msg.get("text") == "/status":
                            await send_tg("🟢 v16.2.3 STATUS: Operational.\nPulse: Active.")
            except: pass
            await asyncio.sleep(1)

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ONLINE")
    def log_message(self, *a): pass

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(predator_scanner()), daemon=True).start()
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever(), daemon=True).start()
    asyncio.run(command_listener())
