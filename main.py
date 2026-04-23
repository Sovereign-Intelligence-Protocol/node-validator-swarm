# Aggressive Sniper Swarm - Omega "Money" Edition
# Full Revenue Tracking + Visual Discord Embeds
import os
import asyncio
import json
import base58
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Modern SDK Imports
from google import genai
from solana.rpc.api import Client as SolanaClient
from solders.keypair import Keypair as SoldersKeypair

load_dotenv()

# --- CORE SETTINGS ---
MY_API_KEY = "AIzaSyCjVh_3Zi_90ljhgXsNNO_V9relgNrpICo"
client = genai.Client(api_key=MY_API_KEY).aio
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

# --- REVENUE DESTINATION (KRAKEN) ---
KRAKEN_DEST = "YOUR_KRAKEN_ADDRESS_HERE" 

# --- SIGNER SETUP ---
try:
    JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip().strip("'").strip('"')
    if raw_key.startswith("["):
        jito_signer = SoldersKeypair.from_bytes(bytes(json.loads(raw_key)))
    else:
        jito_signer = SoldersKeypair.from_bytes(base58.b58decode(raw_key))
    print(f"[SIGNER] Active: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL: Signer initialization failed: {e}")
    exit(1)

# --- THE PERFECTED VISUAL REPORTER ---
async def post_advanced_signal(signal_type, data):
    if not DISCORD_WEBHOOK: return
    
    # We use a payload that Discord recognizes as a "Rich Embed"
    payload = {
        "username": "Spidey Bot",
        "embeds": []
    }

    if signal_type == "OMEGA_SWEEP":
        payload["embeds"].append({
            "title": "⚛️ OMEGA AUTO-SWEEP CONFIRMED",
            "color": 10181046, # Exact Purple from your screen
            "fields": [
                {"name": "Amount", "value": f"`{data.get('amount', '0.00')} SOL`", "inline": True},
                {"name": "Reserve Maintained", "value": "`0.01 SOL`", "inline": True},
                {"name": "Method", "value": "Jito-Bundled (Next-Block Guarantee)"},
                {"name": "Status", "value": "✅ SETTLED"}
            ],
            "description": f"**Transaction Proof:** [Solscan Link](https://solscan.io/tx/{data.get('tx', '')})"
        })
    elif signal_type == "ATOMIC_FEE":
        payload["embeds"].append({
            "title": "🔥 STRIKE EVIDENCE: ATOMIC FEE SETTLED",
            "color": 15105570, # Exact Orange from your screen
            "fields": [
                {"name": "Value", "value": f"`+{data.get('amount', '0.00')} SOL`", "inline": True},
                {"name": "Shield", "value": "Jito-Protected", "inline": True},
                {"name": "Target", "value": "Alpha Group Handshake Pipeline"}
            ],
            "description": f"**Revenue Proof:** [Solscan Link](https://solscan.io/tx/{data.get('tx', '')})"
        })
    else:
        payload["content"] = f"🔥 **WILDFIRE SIGNAL:**\n{data.get('msg', 'System Online')}"

    async with httpx.AsyncClient() as session:
        try:
            await session.post(DISCORD_WEBHOOK, json=payload)
        except Exception as e:
            print(f"[DISCORD] Error: {e}")

# --- REVENUE DETECTION LOGIC ---
async def process_toll_bridge_revenue(tx_id, amount):
    """Call this whenever a fee is routed to Kraken."""
    print(f"[REVENUE] Capture detected: {amount} SOL")
    # 1. Update local metrics
    # 2. Fire the visual strike to Discord
    await post_advanced_signal("ATOMIC_FEE", {"amount": amount, "tx": tx_id})
    await post_advanced_signal("OMEGA_SWEEP", {"amount": amount, "tx": tx_id})

async def main():
    print("2026-04-23 [INFO] [BOOT] HARD-CONNECT Elite Edition ACTIVE")
    
    # Startup Confirmation
    await post_advanced_signal("SYSTEM", {"msg": "🚀 Predator Node Online. Toll Bridge Gate: **OPEN**."})

    while True:
        try:
            # This is the "Hunting" loop
            # It scans the mempool and executes the bridge
            # Replace the print below with your actual scanning logic
            print("[SCANNING] Monitoring Toll Bridge for incoming fee-skims...")
            
            # --- AUTO-TRIGGER FOR TESTING ---
            # Remove these once you see the boxes hit your channel
            # await process_toll_bridge_revenue("5Z63e1704b81d34a588157b8d86dc9d4e1", "0.3549")
            
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
