import os, asyncio, threading, base58, json, httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- INFRASTRUCTURE & PORT (PORT) ---
PORT = int(os.environ.get("PORT", 10000))
def run_srv():
    h = type('H', (BaseHTTPRequestHandler,), {
        'do_GET': lambda s: (s.send_response(200), s.end_headers(), s.wfile.write(b"OK"))
    })
    HTTPServer(('0.0.0.0', PORT), h).serve_forever()
threading.Thread(target=run_srv, daemon=True).start()

# --- TELEGRAM COMMAND CENTER (Integrated Labels) ---
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
WH = os.environ.get("SOLANA_WALLET_ADDRESS")
# Toll setting derived from your JITO_TIP_AMOUNT or custom
TOLL_AMOUNT = os.environ.get("JITO_TIP_AMOUNT", "0.05") 

async def send_tg_msg(message):
    if not TG_TOKEN or not TG_ADMIN: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_ADMIN, "text": message, "parse_mode": "HTML"}
    async with httpx.AsyncClient() as client:
        try: await client.post(url, json=payload)
        except Exception: pass

async def get_tg_updates():
    """Toll Bridge Listener with full variable awareness"""
    last_id = 0
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(url, params={"offset": last_id + 1, "timeout": 30})
                data = resp.json()
                for result in data.get("result", []):
                    last_id = result["update_id"]
                    msg = result.get("message", {}).get("text", "").lower()
                    if any(x in msg for x in ["pay", "toll", "bridge"]):
                        await send_tg_msg(
                            f"<b>SIP Toll Bridge Active</b>\n\n"
                            f"Deposit: <code>{TOLL_AMOUNT} SOL</code>\n"
                            f"To: <code>{WH}</code>\n"
                            f"Live Trading: {'Enabled' if os.environ.get('LIVE_TRADING') == 'True' else 'Disabled'}\n\n"
                            f"Paste your TX signature to verify."
                        )
            except Exception: pass
            await asyncio.sleep(5)

# --- OPERATIONAL CORE (Locked Variable Mapping) ---
RPC = os.environ.get("RPC_URL")
WSS = os.environ.get("WSS_URL")
PK = os.environ.get("PRIVATE_KEY")
JITO_SIGNER = os.environ.get("JITO_SIGNER_PRIVATE_KEY")

async def predator_scanner():
    asyncio.create_task(get_tg_updates())
    async with AsyncClient(RPC) as client:
        # Initial Alert includes Live status
        status_icon = "🟢" if os.environ.get("LIVE_TRADING") == "True" else "🟡"
        await send_tg_msg(f"<b>SIP Online {status_icon}</b>\nTarget: <code>{WH}</code>\nMode: {'LIVE' if os.environ.get('LIVE_TRADING') == 'True' else 'Simulation'}")
        
        while True:
            try:
                print(f"Pulse: Scanning via {RPC}...")
                # Adaptive protocol check
                if os.environ.get("ADAPTIVE_PROTOCOL_ENABLED") == "True":
                    pass # Custom adaptive logic here
                
                await asyncio.sleep(120) 
            except Exception as e:
                await send_tg_msg(f"<b>Alert:</b> {e}")
                await asyncio.sleep(10)

async def main():
    if not PK: return print("Missing PRIVATE_KEY")
    await predator_scanner()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
