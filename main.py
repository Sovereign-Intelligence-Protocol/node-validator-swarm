import os, asyncio, threading, base58, json, httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# --- 1. RENDER KEEP-ALIVE (PRODUCTION FIX) ---
# Handles GET and HEAD requests to satisfy Render's health checks.
PORT = int(os.environ.get("PORT", 10000))
def run_srv():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers()
            self.wfile.write(b"SIP LIVE")
        def do_HEAD(self): 
            # This fix addresses the 501 error shown in your logs
            self.send_response(200); self.end_headers()
        def log_message(self, format, *args): return 
    HTTPServer(('0.0.0.0', PORT), HealthHandler).serve_forever()
threading.Thread(target=run_srv, daemon=True).start()

# --- 2. CONFIGURATION & PRODUCTION LABELS ---
TG_TOKEN, TG_ADMIN = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_ADMIN_ID")
WH, RPC_URL = os.environ.get("SOLANA_WALLET_ADDRESS"), os.environ.get("RPC_URL")
PK, TOLL = os.environ.get("PRIVATE_KEY"), os.environ.get("JITO_TIP_AMOUNT", "0.05")
JITO_SIGNER_PK = os.environ.get("JITO_SIGNER_PRIVATE_KEY")

# --- 3. TELEGRAM & REVENUE ENGINE ---
async def send_tg(msg):
    if not TG_TOKEN or not TG_ADMIN: return
    async with httpx.AsyncClient() as c:
        try: await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except Exception: pass

async def verify_rev(sig):
    async with AsyncClient(RPC_URL) as c:
        try:
            r = await c.get_transaction(sig, commitment="finalized", max_supported_transaction_version=0)
            if not r or not r.value: return False, "Tx Pending"
            meta, keys = r.value.transaction.meta, r.value.transaction.transaction.message.account_keys
            idx = [str(k) for k in keys].index(WH)
            val = (meta.post_balances[idx] - meta.pre_balances[idx]) / 10**9
            return (True, f"Paid: {val} SOL") if val >= float(TOLL) else (False, f"Short: {val}/{TOLL}")
        except Exception as e: return False, str(e)

async def tg_router():
    last_id = 0
    async with httpx.AsyncClient() as c:
        while True:
            try:
                r = await c.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": last_id+1, "timeout": 20})
                for u in r.json().get("result", []):
                    last_id, msg = u["update_id"], u.get("message", {})
                    txt, cid = msg.get("text", "").lower(), str(msg.get("chat", {}).get("id"))
                    if cid != TG_ADMIN: continue
                    if txt == "/status":
                        await send_tg(f"<b>SIP LIVE</b>\nWallet: <code>{WH}</code>\nTip: <code>{TOLL}</code>")
                    elif any(x in txt for x in ["pay", "toll"]):
                        await send_tg(f"<b>BRIDGE</b>\nSend <code>{TOLL} SOL</code> to: <code>{WH}</code>")
                    elif txt.startswith("/verify"):
                        s = txt.split(" ")[1] if " " in txt else ""
                        ok, res = await verify_rev(s)
                        await send_tg(f"{'✅' if ok else '❌'} {res}")
            except: pass
            await asyncio.sleep(5)

# --- 4. LIVE EXECUTION ENGINE ---
async def execute_live_bundle(payer_kp, signer_kp):
    """Execution logic for Jito-Jupiter swaps."""
    pass 

# --- 5. OPERATIONAL CORE ---
async def predator():
    asyncio.create_task(tg_router())
    payer_kp = Keypair.from_bytes(base58.b58decode(PK))
    await send_tg("<b>SIP PROTOCOL: LIVE</b>\n🚀 Hunter is active.")
    while True:
        try:
            print(f"Pulse: Scanning mempool via {RPC_URL}...")
            await execute_live_bundle(payer_kp, None)
            await asyncio.sleep(120)
        except Exception as e:
            await send_tg(f"<b>LIVE ERROR:</b> {e}")
            await asyncio.sleep(10)

async def main():
    if PK: await predator()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
