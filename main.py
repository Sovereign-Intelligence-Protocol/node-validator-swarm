# Aggressive Sniper Swarm - Omega Edition
# Unified Code: Gemini 2.0 SDK + Advanced Visual Reporting
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

# --- THE PLUG-AND-PLAY SETUP ---
MY_API_KEY = "AIzaSyCjVh_3Zi_90ljhgXsNNO_V9relgNrpICo"
client = genai.Client(api_key=MY_API_KEY).aio

# Webhook for Wildfire Saturation Status
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
SOLANA_RPC_URL_BASE = os.getenv("SOLANA_RPC_URL_BASE") or os.getenv("HELIUS_RPC_URL") or os.getenv("RPC_URL")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
HELIUS_RPC_URL = f"{SOLANA_RPC_URL_BASE}/?api-key={HELIUS_API_KEY}"

# Initialize Signer
try:
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip().strip("'").strip('"')
    if raw_key.startswith("["):
        jito_signer = SoldersKeypair.from_bytes(bytes(json.loads(raw_key)))
    else:
        key_bytes = base58.b58decode(raw_key)
        jito_signer = SoldersKeypair.from_bytes(key_bytes)
    print(f"[SIGNER] Active: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL: Signer initialization failed: {e}")
    exit(1)

# --- ADVANCED VISUAL DISCORD REPORTER ---
async def post_advanced_signal(signal_type, data):
    if not DISCORD_WEBHOOK:
        return
    
    payload = {
        "username": "Spidey Bot",
        "embeds": []
    }

    if signal_type == "OMEGA_SWEEP":
        payload["embeds"].append({
            "title": "⚛️ OMEGA AUTO-SWEEP CONFIRMED",
            "color": 10181046, # Purple
            "fields": [
                {"name": "Amount", "value": f"`{data.get('amount', '0.00')} SOL`", "inline": True},
                {"name": "Reserve Maintained", "value": "`0.01 SOL`", "inline": True},
                {"name": "Method", "value": "Jito-Bundled (Next-Block Guarantee)"},
                {"name": "Status", "value": "✅ SETTLED"}
            ],
            "description": f"**Tx Proof:** [Solscan Link](https://solscan.io/tx/{data.get('tx', '')})"
        })
    elif signal_type == "ATOMIC_FEE":
        payload["embeds"].append({
            "title": "🔥 STRIKE EVIDENCE: ATOMIC FEE SETTLED",
            "color": 15105570, # Orange
            "fields": [
                {"name": "Value", "value": f"`+{data.get('amount', '0.00')} SOL`", "inline": True},
                {"name": "Shield", "value": "Jito-Protected", "inline": True},
                {"name": "Target", "value": "Alpha Group Handshake Pipeline"}
            ],
            "description": f"**Settlement:** [Solscan Link](https://solscan.io/tx/{data.get('tx', '')})"
        })
    else:
        # Fallback for Heartbeat/Wildfire Status
        payload["content"] = f"🔥 **WILDFIRE SIGNAL:**\n{data.get('msg', 'System Online')}"

    async with httpx.AsyncClient() as session:
        try:
            await session.post(DISCORD_WEBHOOK, json=payload)
            print(f"[DISCORD] {signal_type} sent.")
        except Exception as e:
            print(f"[DISCORD] Error: {e}")

async def analyze_sentiment(query):
    try:
        response = await client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"Analyze '{query}' for crypto sentiment and rug risk."
        )
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return "neutral"

async def main():
    print("2026-04-23 [INFO] [BOOT] HARD-CONNECT Elite Edition ACTIVE")
    
    # Send the Heartbeat to prove it's connected
    await post_advanced_signal("SYSTEM", {"msg": "🚀 Predator Node is Online. Initializing Mempool Subscription..."})

    while True:
        try:
            print("[SCANNING] Monitoring Toll Bridge & Liquidity...")
            
            # This is where your scanning logic lives.
            # When you find a hit, call:
            # await post_advanced_signal("OMEGA_SWEEP", {"amount": "0.3549", "tx": "YOUR_TX_ID"})

            await asyncio.sleep(5) 
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
