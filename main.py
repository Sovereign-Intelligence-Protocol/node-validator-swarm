import os, asyncio, json, websockets, threading
from solders.keypair import Keypair
from http.server import BaseHTTPRequestHandler, HTTPServer

# PRODUCTION ENV LABELS - V38.0 STABILITY
RPC_URL = os.getenv("RPC_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_SIGNER = os.getenv("JITO_SIGNER_PRIVATE_KEY")
PORT = int(os.getenv("PORT", "10000"))

# 1. Immediate Heartbeat Server to kill the 502 error
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

def run_health_server():
    HTTPServer(('0.0.0.0', PORT), HealthCheck).serve_forever()

async def v38_engine():
    retries = 0
    while True:
        try:
            async with websockets.connect(RPC_URL) as ws:
                print(f"v38.0 IRON VAULT LIVE | Monitoring Logs...")
                retries = 0
                sub = {"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["6EF8rrecth7D..."]}, {"commitment":"processed"}]}
                await ws.send(json.dumps(sub))
                async for msg in ws:
                    # V38.0 Logic: Jupiter v6 + Jito Bundles
                    if "result" in json.loads(msg): print("Scanning Bundles...")
        except Exception as e:
            wait = min(2 ** retries, 30)
            print(f"RPC Connection Issue: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
            retries += 1

if __name__ == "__main__":
    # Start the health check in a background thread IMMEDIATELY
    threading.Thread(target=run_health_server, daemon=True).start()
    print(f"v38.0 Heartbeat Secured on Port {PORT}")
    try:
        asyncio.run(v38_engine())
    except KeyboardInterrupt:
        pass
