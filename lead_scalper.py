# Lead Scalper Bot - Production Deployment (Ohio optimized)
# Deployment timestamp: 2026-04-22 04:58 AM
# Refactored: Definitive Jito signer initialization
import os
import time
import asyncio
import json
import hashlib
import re
import base58
from datetime import datetime
from dotenv import load_dotenv

import httpx
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey as PublicKey
from solders.keypair import Keypair

# Load environment variables
load_dotenv()

# --- HARDCODED FAIL-SAFE CONFIGURATION ---
HARDCODED_CONFIG = {
    "GOOGLE_API_KEY": "AIzaSyCjVh_3Zi_90IjhgXsNN0_V9relgNrplCo",
    "HELIUS_API_KEY": "e4fbf95c-a828-44ec-bfdb-07be33d18c03",
    "SOLANA_RPC_URL_BASE": "https://mainnet.helius-rpc.com",
    "JITO_SIGNER_PRIVATE_KEY": "DfFBkgk9Lyy6SonLKhCafDUg7nhPiG92xCHV1JPgEWfBu3hhpDz1TVrFoafbwGei7zZB5Go34Wf97wZSdY1Pjvf",
    "SOLANA_WALLET_ADDRESS": "junTtoquNLdo4PFeC7JbH6Mzj7aztaTckK4dQnZ3",
    "CONFIDENCE_THRESHOLD": 0.85,
    "JITO_TIP_AMOUNT": 0.001
}

# Support multiple environment variable names
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or HARDCODED_CONFIG["GOOGLE_API_KEY"]
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY") or os.getenv("I_KEY") or HARDCODED_CONFIG["HELIUS_API_KEY"]
SOLANA_RPC_URL_BASE = os.getenv("SOLANA_RPC_URL_BASE") or os.getenv("HELIUS_RPC_URL") or os.getenv("C_URL") or os.getenv("RPC_URL") or HARDCODED_CONFIG["SOLANA_RPC_URL_BASE"]
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY") or HARDCODED_CONFIG["JITO_SIGNER_PRIVATE_KEY"]
SOLANA_WALLET_ADDRESS = os.getenv("SOLANA_WALLET_ADDRESS") or HARDCODED_CONFIG["SOLANA_WALLET_ADDRESS"]
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD") or HARDCODED_CONFIG["CONFIDENCE_THRESHOLD"])
JITO_TIP_AMOUNT = float(os.getenv("JITO_TIP_AMOUNT") or HARDCODED_CONFIG["JITO_TIP_AMOUNT"])

print(f"[BOOT] GOOGLE_API_KEY length: {len(GOOGLE_API_KEY)}")
print(f"[BOOT] HELIUS_API_KEY length: {len(HELIUS_API_KEY)}")
print(f"[BOOT] SOLANA_RPC_URL_BASE: {SOLANA_RPC_URL_BASE}")
print(f"[BOOT] JITO_SIGNER_PRIVATE_KEY length: {len(JITO_SIGNER_PRIVATE_KEY)}")
print(f"[BOOT] SOLANA_WALLET_ADDRESS: {SOLANA_WALLET_ADDRESS}")
print(f"[BOOT] JITO_SIGNER_PRIVATE_KEY (at runtime): {JITO_SIGNER_PRIVATE_KEY[:5]}...{JITO_SIGNER_PRIVATE_KEY[-5:]}")

JITO_BLOCK_ENGINE_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
HELIUS_RPC_URL = f"{SOLANA_RPC_URL_BASE}/?api-key={HELIUS_API_KEY}"

# Configure Jito Signer
jito_signer = None
try:
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip().strip("'").strip('"')
    if raw_key.startswith("["):
        key_bytes = bytes(json.loads(raw_key))
        jito_signer = Keypair.from_bytes(key_bytes)
    else:
        key_bytes = base58.b58decode(raw_key)
        if len(key_bytes) == 64:
            jito_signer = Keypair.from_bytes(key_bytes)
        elif len(key_bytes) == 32:
            jito_signer = Keypair.from_seed(key_bytes)
        else:
            raise ValueError(f"Invalid key length: {len(key_bytes)} bytes")
    
    if jito_signer:
        print(f"[SIGNER] Jito signer initialized successfully: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL ERROR: Jito signer initialization failed: {e}")

# --- Advanced Filtering Parameters ---
MIN_LIQUIDITY_THRESHOLD = 250000
MIN_GEMINI_CONFIDENCE_SCORE = int(CONFIDENCE_THRESHOLD * 100)
POLLING_INTERVAL_SECONDS = 2
MIN_SOL_RESERVE = 0.02
MAX_JITO_TIP_SOL = JITO_TIP_AMOUNT
sentiment_cache = {}

async def call_helius_rpc(method: str, params: list) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient() as client:
        response = await client.post(HELIUS_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_wallet_balance() -> float:
    if not jito_signer:
        print("[WALLET] Jito signer is None. Cannot fetch balance.")
        return 0.0
    try:
        pubkey_str = str(jito_signer.pubkey())
        print(f"[WALLET] Fetching balance for {pubkey_str}...")
        result = await call_helius_rpc("getBalance", [pubkey_str])
        if "result" in result:
            balance_sol = result["result"]["value"] / 1e9
            print(f"[WALLET] Current Balance: {balance_sol:.9f} SOL")
            return balance_sol
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
    return 0.0

async def analyze_social_sentiment(query: str) -> tuple:
    try:
        headers = {"Content-Type": "application/json"}
        prompt = f"Analyze crypto token '{query}' for sentiment and rug risk. Provide Sentiment (positive/neutral/negative), Confidence (1-100), and Risk of Rug (0-100%)."
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            text = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").lower()
            
            sentiment = "positive" if "positive" in text else "negative" if "negative" in text else "neutral"
            confidence = 0
            match = re.search(r"confidence:\s*(\d+)", text)
            if match: confidence = int(match.group(1))
            
            return sentiment, confidence
    except:
        return "neutral", 0

async def run_scalper():
    print("Lead Scalper Bot Initializing...")
    while True:
        try:
            balance = await get_wallet_balance()
            if balance >= MIN_SOL_RESERVE:
                print("Bot initialized and Rent Guard PASSED")
                sentiment, confidence = await analyze_social_sentiment("SOL")
                if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                    print(f"!!! GOLDEN OPPORTUNITY (Confidence: {confidence}) !!!")
            else:
                print(f"[RENT GUARD] Insufficient SOL ({balance:.6f}). Need {MIN_SOL_RESERVE}. Skipping.")

            print(f"Scanning... (next in {POLLING_INTERVAL_SECONDS}s)")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_scalper())
