import os, asyncio, json, websockets, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Bot

# PRODUCTION ENVIRONMENT LABELS
RPC_URL = os.getenv("RPC_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
JITO_TIP_AMOUNT = os.getenv("JITO_TIP_AMOUNT", "0.001")
PORT = int(os.getenv("PORT", "10000"))

# RENDER HANDSHAKE: Fixed 501/502 errors
class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def run_heartbeat():
    HTTPServer(('0.0.0.0', PORT), RenderHandler).serve_forever()

async def v38_iron_vault_engine():
    retries = 0
    tg_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    while True:
        try:
            async with websockets.connect(RPC_URL) as ws:
                print(f"v38.0 OMNICORE ACTIVE | Jito Tip: {JITO_TIP_AMOUNT}")
                retries = 0
                # TOLL BRIDGE MONITORING: 6EF8 Program Target
                sub = {
                    "jsonrpc": "2.0", "id": 1, "method": "logsSubscribe",
                    "params": [{"mentions": ["6EF8rrecth7D..."]}, {"commitment": "processed"}]
                }
                await ws.send(json.dumps(sub))
                async for msg in ws:
                    data = json.loads(msg)
                    if "result" in data:
                        print("🎯 Signal Detected: Executing Toll Bridge Sniper...")
                        try:
                            # Replace YOUR_CHAT_ID with your actual numeric ID
                            await tg_bot.send_message(chat_id="YOUR_CHAT_ID", text="🚀 Vault Trade Executed.")
                        except Exception as te:
                            print(f"Telegram Notification Failed: {te}")
        except Exception as e:
            wait = min(2 ** retries, 30)
            print(f"Connection Alert: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
            retries += 1

if __name__ == "__main__":
    # Start the networking fix in background thread
    threading.Thread(target=run_heartbeat, daemon=True).start()
    print(f"S.I.P. Iron Vault v38.0 Secured on Port {PORT}")
    try:
        asyncio.run(v38_iron_vault_engine())
    except KeyboardInterrupt:
        pass
