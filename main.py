# Lead Scalper Bot - Final Unified Migration
# Refactored for google-genai SDK (Gemini 2.0 Flash)
import os
import time
import asyncio
import json
import re
import base58
import httpx
from dotenv import load_dotenv

# Modern SDK Imports
from google import genai
from solana.rpc.api import Client as SolanaClient
from solders.keypair import Keypair as SoldersKeypair

load_dotenv()

# --- Setup ---
# Automatically detects GOOGLE_API_KEY from Render environment
client = genai.Client()
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY") or os.getenv("I_KEY")
SOLANA_RPC_URL_BASE = os.getenv("SOLANA_RPC_URL_BASE") or os.getenv("HELIUS_RPC_URL") or os.getenv("RPC_URL")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
JITO_BLOCK_ENGINE_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"

# Initialize Signer
try:
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip().strip("'").strip('"')
    if raw_key.startswith("["):
        jito_signer = SoldersKeypair.from_bytes(bytes(json.loads(raw_key)))
    else:
        key_bytes = base58.b58decode(raw_key)
        jito_signer = SoldersKeypair.from_bytes(key_bytes) if len(key_bytes) != 32 else SoldersKeypair.from_seed(key_bytes)
    print(f"[SIGNER] Active: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL: Signer initialization failed: {e}")
    exit(1)

HELIUS_RPC_URL = f"{SOLANA_RPC_URL_BASE}/?api-key={HELIUS_API_KEY}"

# --- Logic ---
async def call_rpc(method, params):
    async with httpx.AsyncClient() as h_client:
        response = await h_client.post(HELIUS_RPC_URL, json={"jsonrpc":"2.0","id":1,"method":method,"params":params})
        return response.json()

async def analyze_sentiment(query):
    try:
        prompt = f"Analyze '{query}' for crypto sentiment and rug risk. Format: Sentiment: [positive/neutral/negative], Confidence: [1-100], Risk: [0-100%]"
        # Low-latency Gemini 2.0 Flash call
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = response.text.lower()
        conf = int(re.search(r"confidence:\s*(\d+)", text).group(1)) if "confidence" in text else 0
        risk = int(re.search(r"risk:\s*(\d+)", text).group(1)) if "risk" in text else 100
        return ("positive" if "positive" in text else "neutral"), (conf if risk <= 15 else 0)
    except:
        return "neutral", 0

async def main():
    print("HARD-CONNECT Elite Edition ACTIVE") # Confirming boot
    while True:
        try:
            res = await call_rpc("getBalance", [str(jito_signer.pubkey())])
            balance = res["result"]["value"] / 1e9
            
            if balance >= 0.02:
                sentiment, confidence = await analyze_sentiment("SOL")
                if sentiment == "positive" and confidence >= 85:
                    print(f"!!! OPPORTUNITY DETECTED ({confidence}%) !!!")
            else:
                print(f"[RENT GUARD] Low Balance: {balance:.4f} SOL")

            await asyncio.sleep(2)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
