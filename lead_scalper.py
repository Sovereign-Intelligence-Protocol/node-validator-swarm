# Lead Scalper Bot - Production Deployment (Ohio optimized)
# Deployment timestamp: 2026-04-22 04:55 AM
# Refactored: Ultra-robust Jito signer initialization and merged fail-safe config
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
# These values are used if environment variables are missing
HARDCODED_CONFIG = {
    "GOOGLE_API_KEY": "AIzaSyCjVh_3Zi_90IjhgXsNN0_V9relgNrplCo",
    "HELIUS_API_KEY": "e4fbf95c-a828-44ec-bfdb-07be33d18c03",
    "SOLANA_RPC_URL_BASE": "https://mainnet.helius-rpc.com",
    "JITO_SIGNER_PRIVATE_KEY": "DfFBkgk9Lyy6SonLKhCafDUg7nhPiG92xCHV1JPgEWfBu3hhpDz1TVrFoafbwGei7zZB5Go34Wf97wZSdY1Pjvf",
    "SOLANA_WALLET_ADDRESS": "junTtoquNLdo4PFeC7JbH6Mzj7aztaTckK4dQnZ3",
    "CONFIDENCE_THRESHOLD": 0.85,
    "JITO_TIP_AMOUNT": 0.001
}

# Support multiple environment variable names for maximum flexibility
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

JITO_BLOCK_ENGINE_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"

# Gemini API configuration
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"

# Configure Helius RPC client
HELIUS_RPC_URL = f"{SOLANA_RPC_URL_BASE}/?api-key={HELIUS_API_KEY}"

# Configure Solana RPC client
solana_client = SolanaClient(HELIUS_RPC_URL)

# Configure Jito Signer
jito_signer = None
try:
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip().strip("'").strip('"')
    
    if raw_key.startswith("["):
        key_list = json.loads(raw_key)
        key_bytes = bytes(key_list)
        jito_signer = Keypair.from_bytes(key_bytes)
    else:
        key_bytes = base58.b58decode(raw_key)
        if len(key_bytes) == 32:
            jito_signer = Keypair.from_seed(key_bytes)
        elif len(key_bytes) == 64:
            jito_signer = Keypair.from_bytes(key_bytes)
        else:
            raise ValueError(f"Invalid Jito signer private key length: {len(key_bytes)} bytes")
    
    print(f"[SIGNER] Jito signer initialized successfully: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize Jito signer from provided key: {e}")
    jito_signer = None

# --- Advanced Filtering Parameters ---
MIN_LIQUIDITY_THRESHOLD = 250000
MIN_GEMINI_CONFIDENCE_SCORE = int(CONFIDENCE_THRESHOLD * 100)
POLLING_INTERVAL_SECONDS = 2
MIN_SOL_RESERVE = 0.02
PROJECTED_PROFIT_USD = 5
MAX_GAS_FEE_PERCENTAGE = 0.20
JITO_CONFIDENCE_THRESHOLD = 90
JITO_TIP_PERCENTAGE = 0.10
MAX_JITO_TIP_SOL = JITO_TIP_AMOUNT
SENTIMENT_CACHE_TTL = 300
sentiment_cache = {}

async def call_helius_rpc(method: str, params: list) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient() as client:
        response = await client.post(HELIUS_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_wallet_balance() -> float:
    if jito_signer is None:
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
    current_time = time.time()
    if query in sentiment_cache and (current_time - sentiment_cache[query]["timestamp"] < SENTIMENT_CACHE_TTL):
        return sentiment_cache[query]["sentiment"], sentiment_cache[query]["confidence"]

    try:
        headers = {"Content-Type": "application/json"}
        prompt = f"""Analyze the following crypto token for sentiment and potential \"rug pull\" risk.
        Token: \'{query}\'

        Evaluate these factors:
        1.  **Developer Wallet History:** Look for signs of high-velocity failed launches or suspicious past projects by the same developer.
        2.  **Holder Concentration:** Determine if the top 10 holders control more than 30% of the supply.
        3.  **LP Burn Status:** Is the liquidity pool locked or burned? (Crucial for preventing rug pulls).

        Based on this analysis, provide:
        -   **Sentiment:** [positive/neutral/negative]
        -   **Confidence:** [1-100, reflecting overall positive sentiment and low risk]
        -   **Risk of Rug:** [0-100%, based on developer history, holder concentration, and LP burn status]

        Example Format:
        Sentiment: positive, Confidence: 92, Risk of Rug: 5%
        """
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            text = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").lower()
            
            sentiment, confidence, rug_risk = "neutral", 0, 100
            if "positive" in text: sentiment = "positive"
            elif "negative" in text: sentiment = "negative"
            
            try:
                match = re.search(r"confidence:\s*(\d+)", text)
                if match: confidence = int(match.group(1))

                match_rug = re.search(r"risk of rug:\s*(\d+)%", text)
                if match_rug: rug_risk = int(match_rug.group(1))
            except: pass

            if rug_risk > 15:
                print(f"[GEMINI] High rug risk detected ({rug_risk}%). Setting confidence to 0.")
                confidence = 0

            sentiment_cache[query] = {"sentiment": sentiment, "confidence": confidence, "timestamp": current_time}
            return sentiment, confidence
    except:
        return "neutral", 0

async def send_jito_bundle(transactions: list, confidence_score: int, jito_tip_sol: float = MAX_JITO_TIP_SOL):
    print("[JITO] Submitting bundle...")
    try:
        import base64
        tx_list = [base64.b64encode(tx).decode("utf-8") for tx in transactions]
        payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [tx_list]}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(JITO_BLOCK_ENGINE_URL, json=payload)
            result = response.json()
            if "result" in result:
                print(f"[JITO] Bundle {result['result']} Pending.")
                return result["result"]
    except Exception as e:
        print(f"Jito Error: {e}")
    return None

async def run_scalper():
    print("Lead Scalper Bot Initializing...")
    target_token = "So11111111111111111111111111111111111111112"

    while True:
        try:
            balance = await get_wallet_balance()
            if balance >= MIN_SOL_RESERVE:
                print("Bot initialized and Rent Guard PASSED")
                
                # Hunting Logic
                sentiment, confidence = await analyze_social_sentiment("SOL")
                if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                    print(f"!!! GOLDEN OPPORTUNITY (Confidence: {confidence}) !!!")
                    # Trade execution logic would follow here
                    
                    # Dynamic Jito Tipping Logic
                    current_jito_tip_sol = MAX_JITO_TIP_SOL
                    if confidence >= 95:
                        current_jito_tip_sol *= 1.5
                        print(f"[JITO] Increasing tip to {current_jito_tip_sol:.6f} SOL for high-confidence trade.")

            else:
                print(f"[RENT GUARD] Insufficient SOL ({balance:.6f}). Need {MIN_SOL_RESERVE}. Skipping.")

            print(f"Scanning... (next in {POLLING_INTERVAL_SECONDS}s)")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_scalper())
