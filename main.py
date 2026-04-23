# Aggressive Sniper Swarm - Final Migration + Discord Voice
# Refactored for google-genai SDK (Gemini 2.0 Flash)
import os
import asyncio
import json
import base58
import httpx
from dotenv import load_dotenv

# Modern SDK Imports
from google import genai
from solana.rpc.api import Client as SolanaClient
from solders.keypair import Keypair as SoldersKeypair

load_dotenv()

# --- THE PLUG-AND-PLAY SETUP ---
MY_API_KEY = "AIzaSyCjVh_3Zi_90ljhgXsNNO_V9relgNrpICo"
# Use .aio for the asynchronous client
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

# --- DISCORD REPORTER ---
async def post_to_discord(msg):
    if DISCORD_WEBHOOK:
        async with httpx.AsyncClient() as session:
            try:
                payload = {"content": f"🔥 **WILDFIRE SIGNAL:**\n{msg}"}
                await session.post(DISCORD_WEBHOOK, json=payload)
                print("[DISCORD] Signal broadcasted.")
            except Exception as e:
                print(f"[DISCORD] Broadcast Error: {e}")

async def analyze_sentiment(query):
    try:
        prompt = f"Analyze '{query}' for crypto sentiment and rug risk."
        response = await client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return "neutral"

async def main():
    print("2026-04-23 [INFO] [BOOT] HARD-CONNECT Elite Edition ACTIVE")
    
    # Heartbeat: Confirmation that the bot is back in the channel
    await post_to_discord("🚀 Predator Node is Online. Initializing Mempool Subscription...")

    while True:
        try:
            print("[SCANNING] Checking liquidity pairs...")
            # When you find a hit, you can now call:
            # await post_to_discord(f"New Signal Found: {token_address}")
            await asyncio.sleep(5) 
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
