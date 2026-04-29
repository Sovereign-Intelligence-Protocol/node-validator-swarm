import os, asyncio, httpx, signal, threading, time, base64, json, psycopg2
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ⚙️ CONFIG (Exact Labeling) ---
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
        if PRIV_KEY_STR.startswith("["): return Keypair.from_json(PRIV_KEY_STR)
        return Keypair.from_base58_string(PRIV_KEY_STR)
    except: return None

async def send_tg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": ADMIN_ID, "text": f"🦅 PREDATOR:\n{msg}"})
    except: pass

# --- 🔫 THE TRIGGER (MEV-Shield + Stable Priority) ---
async def fire_swap(target_mint, amount_sol=0.01):
    kp = get_keypair()
    if not kp: return "❌ KEY ERROR"
    
    lamports = int(amount_sol * 10**9)
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            # 1. Jupiter Quote
            q_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={target_mint}&amount={lamports}&slippageBps=100"
            quote = (await client.get(q_url)).json()
            
            # 2. Build Transaction with Priority Fee
            s_res = await client.post("https://quote-api.jup.ag/v6/swap", json={
                "quoteResponse": quote,
                "userPublicKey": str(kp.pubkey()),
                "wrapAndUnwrapSol": True,
                "prioritizationFeeLamports": 25000 
            })
            tx_data = s_res.json().get("swapTransaction")
            
            # 3. Sign & Jito Broadcast
            raw_tx = VersionedTransaction.from_bytes(base64.b64decode(tx_data))
            signature = kp.sign_message(raw_tx.message.to_bytes_versioned())
            signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
            
            jito_url = "https://mainnet.block-engine.jito.wtf/api/v1/transactions"
            payload = {"jsonrpc":"2.0","id":1,"method":"sendTransaction","params":[base64.b64encode(bytes(signed_tx)).decode('utf-8'), {"encoding":"base64"}]}
            
            final = await client.post(jito_url, json=payload)
            res = final.json().get("result")
            return f"🎯 KILL CONFIRMED: https://solscan.io/tx/{res}" if res else "⚠️ Jito Refused"
    except Exception as e: return f"❌ ERROR: {str(e)}"

# --- 🧠 THE SCANNER ---
async def predator_scanner():
    await send_tg("🦅 GOD MODE v16.4: ONLINE.\nBuild Error Resolved.\nShield: MEV-Jito Active.")
    while running:
        try:
            # Scanning for the $31 Golden Opportunity
            target = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # Test Swap
            sig = await fire_swap(target, 0.01)
            if "🎯" in sig:
                await send_tg(sig)
                break 
        except: pass
        await asyncio.sleep(60)

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
                            await send_tg("🟢 v16.4 STATUS: Full God Mode.\nReady for tonight's hunt.")
            except: pass
            await asyncio.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(predator_scanner()), daemon=True).start()
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), type('H',(BaseHTTPRequestHandler,),{'do_GET':lambda s: (s.send_response(200),s.end_headers(),s.wfile.write(b"OK")),'log_message':lambda *a: None})).serve_forever(), daemon=True).start()
    asyncio.run(command_listener())
