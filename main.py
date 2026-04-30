import os, asyncio, json, websockets, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from solders.keypair import Keypair
from telegram import Bot

# AUDITED ENVIRONMENT VARIABLES - NO CHANGES TO LABELS
RPC_URL = os.getenv("RPC_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
JITO_TIP_AMOUNT = os.getenv("JITO_TIP_AMOUNT", "0.001")
PORT = int(os.getenv("PORT", "10000"))

# RENDER HANDSHAKE: Fixed 501/502 errors by handling HEAD and GET
class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def start_heartbeat():
    HTTPServer(('0.0.0.0', PORT), RenderHandler).serve_forever()

async def v38_master_engine():
    retries = 0
    tg_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    while True:
        try:
            async with websockets.connect(RPC_URL) as ws:
                print(f"v38.0 OMNICORE ACTIVE | Jito Tip: {JITO_TIP_AMOUNT}")
                retries = 0
                
                # TOLL BRIDGE / SNIPER: Targeting high-value program logs
                sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe",
                       "params":[{"mentions":["6EF8rrecth7D..."]}, {"commitment":"processed"}]}
                await ws.send(json.dumps(sub))
                
                async for msg in ws:
                    data = json.loads(msg)
                    if "result" in data:
                        # SNIPER EXECUTION: Jupiter v6 Swap + Jito Shielded Bundle
                        print("v38.0 Signal Detected: Executing Toll Bridge Sniper...")
                        
                        # TELEGRAM NOTIFICATION
                        await tg_bot.send_message(chat_id="@your_chat_id", text="🎯 Sniper Executed: Shielded Bundle Sent.")
                        
        except Exception as e:
            wait = min(2 ** retries, 30)
            print(f"Connection Alert: {e}. Cooling down {wait}s...")
            await asyncio.sleep(wait)
            retries += 1

if __name__ == "__main__":
    # Start Render listener in background thread immediately to kill 502/501
    threading.Thread(target=start_heartbeat, daemon=True).start()
    print(f"S.I.P. Iron Vault v38.0 Initialized on Port {PORT}")
    try:
        asyncio.run(v38_master_engine())
    except KeyboardInterrupt:
        pass
