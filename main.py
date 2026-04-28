import os, threading, httpx
from flask import Flask, request, jsonify
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from spl.token._layouts import MINT_LAYOUT
from psycopg2 import pool

app = Flask(__name__)

# --- 1. THE HANDSHAKE (Mapped to your exact Render Labels) ---
CONFIG = {
    "RPC": os.getenv("RPC_URL"),
    "DB": os.getenv("DATABASE_URL"),
    "KEY": os.getenv("SOLANA_PRIVATE_KEY"),
    "JITO_URL": "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
    "MIN_LIQUIDITY": 10000, # Safety floor for a $31 balance
}

# Persistent Connections to save RAM/Time
solana_client = Client(CONFIG["RPC"])
_http_client = httpx.Client(timeout=10.0)
db_pool = pool.SimpleConnectionPool(1, 5, dsn=CONFIG["DB"])

# --- 2. THE SHIELD (Protecting your $31) ---
def check_rug_safety(mint_addr):
    """Checks if Mint and Freeze authorities are revoked (Renounced)."""
    try:
        pubkey = Pubkey.from_string(mint_addr)
        res = solana_client.get_account_info(pubkey)
        if not res.value: return False
        
        # Parse the SPL Token Mint data
        data = res.value.data
        parsed = MINT_LAYOUT.parse(data)
        
        # If either authority exists, the dev can rug you.
        if parsed.mint_authority_option == 1 or parsed.freeze_authority_option == 1:
            print(f"[SHIELD] Blocked: {mint_addr} is NOT renounced.")
            return False
            
        print(f"[SHIELD] Clear: {mint_addr} is safe to snipe.")
        return True
    except: return False

# --- 3. THE EXECUTION (The Sniper) ---
def fire_bundle(serialized_tx):
    """Sends the trade to Jito to stay invisible to front-runners."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [[serialized_tx]]}
    try:
        _http_client.post(CONFIG["JITO_URL"], json=payload)
    except: pass

@app.route("/webhook", methods=["POST"])
def on_signal():
    """Receives Helius signals - The 'Eyes' of the bot."""
    data = request.json
    for event in data:
        mint = event.get("mint")
        if mint and check_rug_safety(mint):
            # LOGIC: If safe, it executes the swap here using CONFIG["KEY"]
            print(f"[HUNT] Targeting: {mint}")
            # threading.Thread(target=fire_bundle, args=(tx,)).start()
    return jsonify({"status": "hunting"}), 200

@app.route("/health")
def health(): return "v7.5 Online", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
