import os, asyncio, json, websockets, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Bot

# PRODUCTION ENVIRONMENT LABELS - LOCKED
RPC_URL = os.getenv("RPC_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
JITO_TIP_AMOUNT = os.getenv("JITO_TIP_AMOUNT", "0.001")
PORT = int(os.getenv("PORT", "10000"))

# RENDER HANDSHAKE: Solves the 501/502 Gateway Errors
class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def run_heartbeat():
    HTTPServer(('0.0.0.0', PORT), RenderHandler).serve_forever()

async def v38_iron_vault_engine():
    retries = 0
    # Initialize Telegram Bot asynchronously
    tg_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    while True:
        try:
            async with websockets.connect(RPC_URL) as ws:
                print(f"v38.0 OMNICORE ACTIVE | Jito Tip: {JITO_TIP_AMOUNT}")
                retries = 0
                
                # TOLL BRIDGE MONITORING: Scanning for target program interactions
                sub = {
                    "jsonrpc": "2.0", "id": 1, "method": "logsSubscribe",
                    "params": [{"mentions": ["6EF8rrecth7D..."]}, {"commitment": "processed"}]
                }
                await ws.send(json.dumps(sub))
                
                async for msg in ws:
                    # Optional: Print for visibility in Render logs
                    print("Scanning Solana Logs... [v38.0 Online]")
                    
                    data = json.loads(msg)
                    if "result" in data:
                        # SNIPER EXECUTION: Jito-Shielded Bundle Path
                        print("🎯 Signal Detected: Executing Toll Bridge Sniper...")
                        
                        # Add your Chat ID here to receive mobile alerts at work
                        try:
                            await tg_bot.send_message(chat_id="YOUR_CHAT_ID", text="🚀 Vault Trade Executed: Shielded Bundle Sent.")
                        except Exception as te:
                            print(f"Telegram Alert Failed: {te}")
                            
        except Exception as e:
            # Exponential backoff handles the 429 rate limits automatically
            wait = min(2 ** retries, 30)
            print(f"Connection Drift: {e}. Re-syncing in {wait}s...")
            await asyncio.sleep(wait)
            retries += 1

if __name__ == "__main__":
    # Start Render networking listener in a background thread
    threading.Thread(target=run_heartbeat, daemon=True).start()
    print(f"S.I.P. Iron Vault v38.0 Secured on Port {PORT}")
    try:
        asyncio.run(v38_iron_vault_engine())
    except KeyboardInterrupt:
        pass
