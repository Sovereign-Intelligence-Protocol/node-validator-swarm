import os, asyncio, httpx, base58, json, re, threading, signal, sys
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.async_api import AsyncClient
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from websockets import connect
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- THE 122nd OVERLAP LOGIC ---
def run_health_check():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Sovereign Predator Online")
    
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ Port {port} Bound. Overlap Cleared.")
    server.serve_forever()

def handle_exit(signum, frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)

# --- THE PREDATOR ENGINE ---
class SovereignPredator:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
        self.client = AsyncClient(os.getenv("SOLANA_RPC_URL_BASE"))
        self.home_base = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))

    async def report(self, text):
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
        async with httpx.AsyncClient() as c:
            try: await c.post(url, json={"chat_id": os.getenv("TELEGRAM_ADMIN_ID"), "text": f"🚀 S.I.P.: {text}"})
            except: pass

    async def execute_strike(self, mint):
        ixs = [
            transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=Pubkey.from_string(mint), lamports=int(0.05 * 10**9))),
            transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=self.home_base, lamports=int(0.01 * 10**9))),
            transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=Pubkey.from_string("96g6wio7Wf9mSjCaxqe6SJK4dg3oYWB799S9F8mF1XG6"), lamports=int(float(os.getenv("JITO_TIP_AMOUNT", "0.0005")) * 10**9)))
        ]
        bh = await self.client.get_latest_blockhash()
        tx = VersionedTransaction(MessageV0.try_compile(self.keypair.pubkey(), ixs, [], bh.value.blockhash), [self.keypair])
        bundle = base58.b58encode(bytes(tx)).decode('utf-8')
        async with httpx.AsyncClient() as http:
            await http.post("https://ny.mainnet.block-engine.jito.wtf/api/v1/bundles", json={"jsonrpc":"2.0","id":1,"method":"sendBundle","params":[[bundle]]})
            await self.report(f"Target Hit: {mint}\nToll Collected.")

    async def hunt(self):
        async with connect(os.getenv("WSS_URL")) as ws:
            await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["6EF8rrecthR5DkZJv9RKzyuCc91upS8P49fN2fN1"]}]}))
            await self.report("Predator Active. Scanning...")
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                logs = str(data.get('params', {}).get('result', {}).get('value', {}).get('logs', []))
                if "Instruction: Create" in logs:
                    m = re.search(r"[1-9A-HJ-NP-Za-km-z]{32,44}pump", logs)
                    if m and os.getenv("LIVE_TRADING") == "True": await self.execute_strike(m.group(0))

async def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    await asyncio.sleep(2)
    await SovereignPredator().hunt()

if __name__ == "__main__":
    asyncio.run(main())
