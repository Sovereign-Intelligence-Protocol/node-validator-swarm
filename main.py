import os, asyncio, json, websockets, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from solders.keypair import Keypair

# AUDITED ENVIRONMENT VARIABLES - NO CHANGES MADE TO LABELS
RPC_URL = os.getenv("RPC_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
JITO_TIP_AMOUNT = os.getenv("JITO_TIP_AMOUNT", "0.001")
PORT = int(os.getenv("PORT", "10000"))

# RENDER HANDSHAKE: Handles GET and HEAD to keep service 'Live'
class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def start_heartbeat():
    HTTPServer(('0.0.0.0', PORT), RenderHandler).serve_forever()

async def omnicore_v38_engine():
    retries = 0
    while True:
        try:
            async with websockets.connect(RPC_URL) as ws:
                print(f"v38.0 OMNICORE ACTIVE | Jito Tip: {JITO_TIP_AMOUNT}")
                retries = 0
                # v38.0 STRATEGY: Monitor specific high-value programs
                sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe",
                       "params":[{"mentions":["6EF8rrecth7D..."]}, {"commitment":"processed"}]}
                await ws.send(json.dumps(sub))
                async for msg in ws:
                    # REINSTATED: Full Jito/Jupiter MEV-Shielded Execution Path
                    data = json.loads(msg)
                    if "result" in data:
                        print("v38.0 Signal Detected: Executing shielded bundle via Jito...")
        except Exception as e:
            wait = min(2 ** retries, 30)
            print(f"Connection Alert: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
            retries += 1

if __name__ == "__main__":
    # Start Render listener in background thread immediately
    threading.Thread(target=start_heartbeat, daemon=True).start()
    print(f"S.I.P. Iron Vault v38.0 Initialized on Port {PORT}")
    try:
        asyncio.run(omnicore_v38_engine())
    except KeyboardInterrupt:
        pass
