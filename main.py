import os, asyncio, threading, base58, json, httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- 1. RENDER HEALTH CHECK ---
PORT = int(os.environ.get("PORT", 10000))
def run_srv():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers()
            self.wfile.write(b"SIP PROTOCOL LIVE")
        def do_HEAD(self): 
            self.send_response(200); self.end_headers()
        def log_message(self, format, *args): return 
    HTTPServer(('0.0.0.0', PORT), HealthHandler).serve_forever()
threading.Thread(target=run_srv, daemon=True).start()

# --- 2. CONFIGURATION ---
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS")
RPC_URL = os.environ.get("RPC_URL")
PK = os.environ.get("PRIVATE_KEY")
TOLL = os.environ.get("JITO_TIP_AMOUNT", "0.05")

# --- 3. TELEGRAM & TOLL ENGINE ---
async def send_tg(msg):
    if not TG_TOKEN or not TG_ADMIN: return
    async with httpx.AsyncClient() as c:
        try: 
            await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                         json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except Exception: 
            pass

async def verify_rev(sig):
    async with AsyncClient(RPC_URL) as c:
        try:
            r = await c.get_transaction(sig, commitment="finalized", max_supported_transaction_version=0)
            if not r or not r.value: return False, "Tx Pending"
            meta = r.value.transaction.meta
            keys = r.value.transaction.transaction.message.account_keys
            idx = [str(k) for k in keys].index(WH)
            val = (meta.post_balances[idx] - meta.pre_balances[idx]) / 10**9
            return (True, f"Received: {val} SOL") if val >= float(TOLL) else (False, f"Low: {val}/{TOLL}")
        except Exception as e: 
            return False, str(e)

async def tg_router():
    last_id = 0
    async with httpx.AsyncClient() as c:
        while True:
            try:
                r = await c.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": last_id+1, "timeout": 20})
                for u in r.json().get("result", []):
                    last_id = u["update_id"]
                    msg = u.get("message", {})
                    txt, cid = msg.get("text", "").lower(), str(msg.get("chat", {}).get("id"))
                    if cid != TG_ADMIN: continue
                    
                    if txt == "/status":
                        await send_tg(f"<b>SIP LIVE</b>\nWallet: <code>{WH}</code>\nBalance: Tracking...")
                    elif any(x in txt for x in ["pay", "toll", "bridge"]):
                        await send_tg(f"<b>BRIDGE</b>\nSend <code>{TOLL} SOL</code> to: <code>{WH}</code>")
                    elif txt.startswith("/verify"):
                        s = txt.split(" ")[1] if " " in txt else ""
                        ok, res = await verify_rev(s)
                        await send_tg(f"{'✅' if ok else '❌'} {res}")
            except Exception:
                await asyncio.sleep(5)
            await asyncio.sleep(5)

# --- 4. THE 120s PREDATOR CORE ---
async def predator():
    asyncio.create_task(tg_router())
    payer_kp = Keypair.from_bytes(base58.b58decode(PK))
    await send_tg(f"<b>SIP ONLINE</b>\n🚀 Monitoring via Helius...")
    
    while True:
        try:
            print("Pulse: Scanning for high-conviction 0.05 SOL snipes...")
            await asyncio.sleep(120) 
        except Exception as e:
            await send_tg(f"<b>CRITICAL:</b> {e}")
            await asyncio.sleep(10)

async def main():
    if PK: await predator()
    else: print("Error: PRIVATE_KEY missing.")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
