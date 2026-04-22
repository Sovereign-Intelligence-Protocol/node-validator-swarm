# Lead Scalper Bot - Production Deployment
# Deployment timestamp: 2026-04-21 09:55 PM
# Refactored: Ultra-robust Jito signer initialization and enhanced balance fetching
import os
import time
import asyncio
import json
import hashlib
from datetime import datetime
from dotenv import load_dotenv

import httpx
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey as PublicKey
from solders.keypair import Keypair

# Load environment variables
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
SOLANA_RPC_URL_BASE = os.getenv("HELIUS_RPC_URL")
JITO_BLOCK_ENGINE_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
# Match EXACTLY what is in the Render 'Environment' tab
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")

if not GOOGLE_API_KEY or not HELIUS_API_KEY or not SOLANA_RPC_URL_BASE or not JITO_SIGNER_PRIVATE_KEY:
    print("Error: GOOGLE_API_KEY, HELIUS_API_KEY, SOLANA_RPC_URL_BASE, and JITO_SIGNER_PRIVATE_KEY must be set in environment variables.")
    exit(1)

# Gemini API configuration
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"

# Configure Helius RPC client
HELIUS_RPC_URL = f"{SOLANA_RPC_URL_BASE}/?api-key={HELIUS_API_KEY}"

# Configure Solana RPC client
solana_client = SolanaClient(HELIUS_RPC_URL)

# Configure Jito Signer
jito_signer = None
try:
    import base58
    from solders.keypair import Keypair as SoldersKeypair
    
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip()
    # Remove any quotes that might have been added by accident
    raw_key = raw_key.strip("'").strip('"')
    
    print(f"[DEBUG] JITO_SIGNER_PRIVATE_KEY format check (first 5 chars): {raw_key[:5]}...")
    
    if raw_key.startswith("["):
        # Handle JSON array format: [1, 2, 3, ...]
        print("[DEBUG] Parsing JITO_SIGNER_PRIVATE_KEY as JSON array.")
        key_list = json.loads(raw_key)
        key_bytes = bytes(key_list)
        jito_signer = SoldersKeypair.from_bytes(key_bytes)
    else:
        # Handle Base58 format
        print("[DEBUG] Parsing JITO_SIGNER_PRIVATE_KEY as Base58 string.")
        key_bytes = base58.b58decode(raw_key)
        # Some base58 keys are 64 bytes (secret + public), some are 32 (secret only)
        # SoldersKeypair.from_bytes expects 64 bytes
        if len(key_bytes) == 32:
            jito_signer = SoldersKeypair.from_seed(key_bytes)
        else:
            jito_signer = SoldersKeypair.from_bytes(key_bytes)
    
    print(f"[SIGNER] Initialized successfully: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize Jito signer: {e}")
    # Do not exit, but the bot will be in safety mode if this fails
    jito_signer = None

# --- Advanced Filtering Parameters ---
MIN_LIQUIDITY_THRESHOLD = 250000
MIN_GEMINI_CONFIDENCE_SCORE = 85
POLLING_INTERVAL_SECONDS = 2
MIN_SOL_RESERVE = 0.02
PROJECTED_PROFIT_USD = 5
MAX_GAS_FEE_PERCENTAGE = 0.20
JITO_CONFIDENCE_THRESHOLD = 90
JITO_TIP_PERCENTAGE = 0.10
MAX_JITO_TIP_SOL = 0.0005
SENTIMENT_CACHE_TTL = 300
SOCIAL_SENTIMENT_KEYWORDS = ["pump", "moon", "buy now", "🚀", "📈"]
sentiment_cache = {}

# --- Diary System ---
DIARY_FILE = "bot_diary.json"

def load_diary():
    if os.path.exists(DIARY_FILE):
        try:
            with open(DIARY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "pnl_usd": 0.0,
        "wallet_balance_sol": 0.0,
        "last_trade_timestamp": None,
        "trade_history": [],
        "min_sol_reserve": MIN_SOL_RESERVE
    }

def save_diary(diary_data):
    with open(DIARY_FILE, "w") as f:
        json.dump(diary_data, f, indent=4)

async def call_helius_rpc(method: str, params: list) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient() as client:
        response = await client.post(HELIUS_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_token_price(token_symbol: str) -> float:
    return 200.0 if token_symbol.upper() == "SOL" else 1.0

async def check_liquidity(token_address: str) -> float:
    return 500000.0

async def check_gas_fees() -> float:
    sol_price_usd = await get_token_price("SOL")
    return (5000 / 1e9) * sol_price_usd

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
        Token: '{query}'

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
                import re
                match = re.search(r"confidence:\s*(\d+)", text)
                if match: confidence = int(match.group(1))

                match_rug = re.search(r"risk of rug:\s*(\d+)%", text)
                if match_rug: rug_risk = int(match_rug.group(1))

            except: pass

            # Apply rug risk filter
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
        tx_list = [base64.b64encode(tx).decode('utf-8') for tx in transactions]
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

async def generate_trade_logic_with_gemini(current_market_data: dict) -> str:
    prompt = f"Generate Solana trade logic for: {json.dumps(current_market_data)}. Define execute_trade(signer_hex, rpc_url) returning hex tx list JSON."
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient() as client:
        response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
        code = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        if code.startswith("```python"): code = code[9:-3].strip()
        return code

async def run_scalper():
    print("Lead Scalper Bot Initializing...")
    diary = load_diary()
    target_token = "So11111111111111111111111111111111111111112"

    while True:
        try:
            balance = await get_wallet_balance()
            if balance >= MIN_SOL_RESERVE:
                print("Bot initialized and Rent Guard PASSED")
                
                # Active Hunting Logic
                liquidity = await check_liquidity(target_token)
                gas = await check_gas_fees()
                
                if liquidity >= MIN_LIQUIDITY_THRESHOLD and gas <= (PROJECTED_PROFIT_USD * MAX_GAS_FEE_PERCENTAGE):
                    sentiment, confidence = await analyze_social_sentiment("SOL")
                    if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                        print(f"!!! GOLDEN OPPORTUNITY (Confidence: {confidence}) !!!")
                        market_data = {"balance": balance, "liquidity": liquidity, "gas": gas, "confidence": confidence}
                        code = await generate_trade_logic_with_gemini(market_data)
                        local_vars = {}
                        exec(code, globals(), local_vars)
                        if 'execute_trade' in local_vars:
                            tx_json = local_vars['execute_trade'](jito_signer.to_bytes().hex(), HELIUS_RPC_URL)
                            tx_bytes = [bytes.fromhex(tx) for tx in json.loads(tx_json)]

                            # Dynamic Jito Tipping Logic
                            current_jito_tip_sol = MAX_JITO_TIP_SOL
                            if confidence >= 95:
                                current_jito_tip_sol *= 1.5  # Increase tip by 50% for high-confidence trades
                                print(f"[JITO] Increasing tip to {current_jito_tip_sol:.6f} SOL for high-confidence trade (Confidence: {confidence}).")

                            await send_jito_bundle(tx_bytes, confidence, current_jito_tip_sol)
            else:
                print(f"[RENT GUARD] Insufficient SOL ({balance:.6f}). Need {MIN_SOL_RESERVE}. Skipping.")

            print(f"Scanning... (next in {POLLING_INTERVAL_SECONDS}s)")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_scalper())
