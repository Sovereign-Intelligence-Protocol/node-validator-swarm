# Aggressive Sniper Swarm - Omega "Money" Edition
import os
import asyncio
import json
import base58
import httpx
from dotenv import load_dotenv

# Modern SDK Imports
from google import genai
from solders.keypair import Keypair as SoldersKeypair

load_dotenv()

# --- CORE SETTINGS ---
MY_API_KEY = os.getenv("GOOGLE_API_KEY") or "AIzaSyCjVh_3Zi_90ljhgXsNNO_V9relgNrpICo"
client = genai.Client(api_key=MY_API_KEY).aio

# --- RENDER ENVIRONMENT SYNC ---
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
KRAKEN_DEST = os.getenv("KRAKEN_DESTINATION") 

# --- SIGNER SETUP (FIXED FOR HEX) ---
try:
    raw_key = os.getenv("SOLANA_PRIVATE_KEY").strip().strip("'").strip('"')
    
    # Check if it's Hex (your screenshots show A-F, 0-9)
    if all(c in "0123456789abcdefABCDEF" for c in raw_key):
        jito_signer = SoldersKeypair.from_bytes(bytes.fromhex(raw_key))
    # Handle Byte Array [1, 2, 3...]
    elif raw_key.startswith("["):
        jito_signer = SoldersKeypair.from_bytes(bytes(json.loads(raw_key)))
    # Default to Base58
    else:
        jito_signer = SoldersKeypair.from_bytes(base58.b58decode(raw_key))
        
    print(f"[SIGNER] Active: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL: Signer initialization failed: {e}")
    exit(1)

# --- THE PERFECTED VISUAL REPORTER ---
async def post_advanced_signal(signal_type, data):
    if not DISCORD_WEBHOOK: return
    payload = {"username": "Spidey Bot", "embeds": []}
    if signal_type == "ATOMIC_FEE":
        payload["embeds"].append({
            "title": "🔥 STRIKE EVIDENCE: ATOMIC FEE SETTLED",
            "color": 15105570,
            "fields": [
                {"name": "Value", "value": f"`+{data.get('amount', '0.00')} SOL`", "inline": True},
                {"name": "Target", "value": "Kraken Vault", "inline": True}
            ],
            "description": f"**Revenue Proof:** [Solscan Link](https://solscan.io/tx/{data.get('tx', '')})"
        })
    else:
        payload["content"] = f"🚀 **{data.get('msg', 'System Online')}**"

    async with httpx.AsyncClient() as session:
        try:
            await session.post(DISCORD_WEBHOOK, json=payload, timeout=10.0)
        except Exception as e:
            print(f"[DISCORD] Error: {e}")

async def main():
    print("2026-04-23 [INFO] [BOOT] HARD-CONNECT Elite Edition ACTIVE")
    await post_advanced_signal("SYSTEM", {"msg": "Predator Node Online. Toll Bridge Gate: OPEN."})

    while True:
        try:
            vault_display = f"{KRAKEN_DEST[:4]}...{KRAKEN_DEST[-4:]}" if KRAKEN_DEST else "NOT_SET"
            print(f"[SCANNING] Monitoring Bridge. Vault: {vault_display}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
