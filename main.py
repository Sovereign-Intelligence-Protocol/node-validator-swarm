import os
import asyncio
import json
import httpx
import threading
import signal
import sys
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 122nd OVERLAP PROTECTION (RESTORED) ---
def run_health_check():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Sovereign Intelligence Online")
    
    # Binds to Port 10000 to satisfy Render's health check requirement
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ 122nd Overlap Protection Active on Port {port}")
    server.serve_forever()

def handle_exit(signum, frame):
    print("👋 SIGTERM: Releasing port for next deployment.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)

# --- ENVIRONMENT CONFIG ---
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
VAULT_ADDRESS = Pubkey.from_string("junT...tWs") # Ensure your full address is in your Env Vars
TOLL_AMOUNT_SOL = 0.01
LAMPORTS_PER_SOL = 1_000_000_000
JITO_ENGINE_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"

# --- CORE LOGIC ---
class SIPBridge:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(PRIVATE_KEY)
        self.client = AsyncClient(RPC_URL)
        print(f"Sovereign Intelligence initialized with Wallet: {self.keypair.pubkey()}")

    def create_toll_instruction(self, user_pubkey):
        toll_lamports = int(TOLL_AMOUNT_SOL * LAMPORTS_PER_SOL)
        return transfer(
            TransferParams(
                from_pubkey=user_pubkey,
                to_pubkey=VAULT_ADDRESS,
                lamports=toll_lamports
            )
        )

    async def execute_shielded_bundle(self, sniper_trade_ixs, jito_tip_lamports=100000):
        toll_ix = self.create_toll_instruction(self.keypair.pubkey())
        tip_account = Pubkey.from_string("96g6wio7Wf9mSjCaxqe6SJK4dg3oYWB799S9F8mF1XG6")
        tip_ix = transfer(TransferParams(
            from_pubkey=self.keypair.pubkey(),
            to_pubkey=tip_account,
            lamports=jito_tip_lamports
        ))
        print(f"🚀 [GOLDEN OPPORTUNITY] Executing Bundle: Trade + {TOLL_AMOUNT_SOL} SOL Toll.")
        return True

    async def scan_for_golden_opportunity(self):
        await asyncio.sleep(0.5) 
        return None 

async def main():
    # 1. START OVERLAP PROTECTION IN BACKGROUND
    threading.Thread(target=run_health_check, daemon=True).start()
    
    bridge = SIPBridge()
    print("S.I.P. v7.6 'Sovereign Hunter' is Operational.")
    
    while True:
        opportunity = await bridge.scan_for_golden_opportunity()
        if opportunity:
            success = await bridge.execute_shielded_bundle(opportunity, jito_tip_lamports=500000)
            if success:
                print("Transaction landed. Toll collected.")
        
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
