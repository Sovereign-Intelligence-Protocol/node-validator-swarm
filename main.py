import os, asyncio, httpx, base58, json, re, threading, signal, sys
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.async_api import AsyncClient
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from websockets import connect
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 122nd OVERLAP HEARTBEAT ---
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

# --- CONFIG ---
RPC_URL = os.getenv("SOLANA_RPC_URL_BASE")
WSS_URL = os.getenv("WSS_URL")
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY")
HOME_BASE = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
JITO_TIP = float(os.getenv("JITO_TIP_AMOUNT", "0.0005"))
LIVE = os.getenv("LIVE_TRADING") == "True"

class SovereignPredator:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(SEED_PK)
        self.client = AsyncClient(RPC_URL)

    async def report(self, text):
        url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as c:
            try: await c.post(url, json={"chat_id": ADMIN_ID, "text": f"🚀 S.I.P.: {text}"})
            except: pass

    async def execute_atomic_bundle(self, mint):
        # Trade (0.05) + Toll (0.01) + Jito Tip
        ixs = [
            transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=Pubkey.from_string(mint), lamports=int(0.05 * 10**9))),
            transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=HOME_BASE, lamports=int(0.01 * 10**9))),
            transfer(TransferParams(from_pubkey=self.keypair.pubkey(), to_pubkey=Pubkey.from_string("96g6wio7Wf9mSjCaxqe6SJK4dg3oYWB799S9F8mF1XG6"), lamports=int(JITO_TIP * 10**9)))
        ]
        bh = await self.client.get_latest_blockhash()
        msg = MessageV0.try_compile(self.keypair.pubkey(), ixs, [], bh.value.blockhash)
        tx = VersionedTransaction(msg, [self.keypair])
        bundle = base58.b58encode(bytes(tx)).decode('utf-8')
        async with httpx.AsyncClient() as http:
            await http.post("https://ny.mainnet.block-engine.jito.wtf/api/v1/bundles", json={"jsonrpc":"2.0","id":1,"method":"sendBundle","params":[[bundle]]})
            await self.report(f"Target Hit: {mint}\n0.01 SOL Toll collected.")

    async def hunt(self):
        async with connect(WSS_URL) as ws:
            await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":["6EF8rrecthR5DkZJv9RKzyuCc91upS8P49fN2fN1"]}]}))
            await self.report("Predator Active. Scanning Mempool...")
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                logs = str(data.get('params', {}).get('result', {}).get('value', {}).get('logs', []))
                if "Instruction: Create" in logs:
                    m = re.search(r"[1-9A-HJ-NP-Za-km-z]{32,44}pump", logs)
                    if m and LIVE: await self.execute_atomic_bundle(m.group(0))

async def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    await asyncio.sleep(2)
    await SovereignPredator().hunt()

if __name__ == "__main__":
    asyncio.run(main())
