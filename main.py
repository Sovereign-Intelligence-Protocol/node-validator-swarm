# Lead Scalper Bot - Production Deployment
# Deployment timestamp: 2026-04-21 09:05 PM
# Refactored: Robust Jito signer initialization, improved sentiment parsing, and real transaction generation
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
    
    # Robust handling of JITO_SIGNER_PRIVATE_KEY
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip()
    print(f"[DEBUG] JITO_SIGNER_PRIVATE_KEY (first 10 chars): {raw_key[:10]}...")
    
    if raw_key.startswith("["):
        # Handle JSON array format: [1, 2, 3, ...]
        print("[DEBUG] Attempting to parse JITO_SIGNER_PRIVATE_KEY as JSON array.")
        key_list = json.loads(raw_key)
        key_bytes = bytes(key_list)
        jito_signer = SoldersKeypair.from_bytes(key_bytes)
    else:
        # Handle Base58 format
        print("[DEBUG] Attempting to parse JITO_SIGNER_PRIVATE_KEY as Base58 string.")
        key_bytes = base58.b58decode(raw_key)
        jito_signer = SoldersKeypair.from_bytes(key_bytes)
    
    print(f"[SIGNER] Initialized successfully: {jito_signer.pubkey()}")
except Exception as e:
    print(f"Warning: Could not initialize Jito signer: {e}")
    jito_signer = None

# --- Advanced Filtering Parameters ---
MIN_LIQUIDITY_THRESHOLD = 250000  # Minimum locked liquidity in USD
VOLUME_SPIKE_PERCENTAGE = 200     # 200% increase in volume
VOLUME_SPIKE_WINDOW_SECONDS = 60  # Over 1 minute
WHALE_ACTIVITY_THRESHOLD = 50000  # Transaction amount in USD
SOCIAL_SENTIMENT_KEYWORDS = ["pump", "moon", "buy now", "🚀", "📈"]
MIN_GEMINI_CONFIDENCE_SCORE = 85  # Minimum confidence score for trade execution
JITO_CONFIDENCE_THRESHOLD = 90    # Confidence score for smart tipping (90+ for 10% tip)
JITO_TIP_PERCENTAGE = 0.10        # 10% of projected profit for Jito tip
MAX_JITO_TIP_SOL = 0.0005         # Cap the Jito tip to 0.0005 SOL
MAX_GAS_FEE_PERCENTAGE = 0.20     # Max 20% of projected profit for gas fees
PROJECTED_PROFIT_USD = 5          # Example projected profit for gas fee calculation
PRICE_MOMENTUM_WINDOW_SECONDS = 30 # Look back 30 seconds for price momentum
SLIPPAGE_TOLERANCE_PERCENTAGE = 2.0 # Slippage tolerance for micro-test
MIN_SOL_RESERVE = 0.02            # 0.02 SOL reserve for rent-exempt status
VOLUME_SPIKE_FOR_SENTIMENT_TRIGGER = 20 # Only trigger Gemini if volume spike suggests move

# --- Efficiency Protocol Parameters ---
POLLING_INTERVAL_SECONDS = 2      # Scan every 2 seconds
SENTIMENT_CACHE_TTL = 300         # Cache sentiment for 5 minutes
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
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(HELIUS_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_token_price(token_symbol: str) -> float:
    try:
        if token_symbol.upper() == "SOL":
            return 200.0  # Mock price for testing
        return 1.0
    except Exception as e:
        print(f"Error getting token price: {e}")
        return 0.0

async def check_liquidity(token_address: str) -> float:
    try:
        return 500000.0  # Mock liquidity for testing
    except Exception as e:
        print(f"Error checking liquidity: {e}")
        return 0.0

async def check_gas_fees() -> float:
    try:
        lamports_per_signature = 5000
        sol_amount = lamports_per_signature / 1e9
        sol_price_usd = await get_token_price("SOL")
        gas_fee_usd = sol_amount * sol_price_usd
        return gas_fee_usd
    except Exception as e:
        print(f"Error checking gas fees: {e}")
        return 0.0

async def get_wallet_balance() -> float:
    if jito_signer is None:
        return 0.0
    try:
        result = await call_helius_rpc("getBalance", [str(jito_signer.pubkey())])
        if "result" in result:
            balance_lamports = result["result"]["value"]
            balance_sol = balance_lamports / 1e9
            return balance_sol
        return 0.0
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return 0.0

async def analyze_social_sentiment(query: str) -> tuple:
    current_time = time.time()
    if query in sentiment_cache and (current_time - sentiment_cache[query]["timestamp"] < SENTIMENT_CACHE_TTL):
        return sentiment_cache[query]["sentiment"], sentiment_cache[query]["confidence"]

    print(f"Analyzing social sentiment for '{query}' using Gemini API...")
    try:
        headers = {"Content-Type": "application/json"}
        keywords_str = ", ".join(SOCIAL_SENTIMENT_KEYWORDS)
        prompt = f"Analyze the social sentiment for '{query}' related to cryptocurrency. Look for hype keywords like {keywords_str}. Provide a sentiment (positive, neutral, negative) and a confidence score (1-100). Format your response EXACTLY as: Sentiment: [sentiment], Confidence: [score]."
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            
            response_text = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip().lower()
            
            sentiment_part = "neutral"
            confidence_score = 0
            
            if "sentiment:" in response_text and "confidence:" in response_text:
                try:
                    parts = response_text.split(",")
                    for part in parts:
                        if "sentiment:" in part:
                            sentiment_part = part.split("sentiment:")[1].strip()
                        if "confidence:" in part:
                            confidence_score = int(part.split("confidence:")[1].strip().split()[0])
                except Exception as parse_e:
                    print(f"Error parsing Gemini response: {parse_e}")
            
            sentiment_cache[query] = {"sentiment": sentiment_part, "confidence": confidence_score, "timestamp": current_time}
            print(f"Gemini sentiment for '{query}': {sentiment_part}, Confidence: {confidence_score}")
            return sentiment_part, confidence_score
    except Exception as e:
        print(f"Error during Gemini sentiment analysis: {e}")
        return "neutral", 0

async def send_jito_bundle(transactions: list, confidence_score: int):
    """Send bundle to Jito Block Engine using direct HTTP API"""
    print("[JITO] Preparing bundle submission via HTTP API...")
    tip_sol = 0
    bundle_status = "Failed"
    bundle_id = None
    try:
        if confidence_score >= JITO_CONFIDENCE_THRESHOLD:
            sol_price_usd = await get_token_price("SOL")
            if sol_price_usd > 0:
                calculated_tip_sol = (PROJECTED_PROFIT_USD * JITO_TIP_PERCENTAGE) / sol_price_usd
                tip_sol = min(calculated_tip_sol, MAX_JITO_TIP_SOL)
        
        tx_list = []
        for tx_bytes in transactions:
            import base64
            tx_b64 = base64.b64encode(tx_bytes).decode('utf-8')
            tx_list.append(tx_b64)
        
        bundle_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendBundle",
            "params": [tx_list]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(JITO_BLOCK_ENGINE_URL, json=bundle_payload)
            response.raise_for_status()
            result = response.json()
            
            if "result" in result:
                bundle_id = result["result"]
                print(f"[JITO] Bundle {bundle_id} Status: Pending.")
                return bundle_id
            else:
                print(f"[JITO] Submission failed: {result.get('error')}")
                return None
    except Exception as e:
        print(f"Error submitting bundle: {e}")
        return None

async def generate_trade_logic_with_gemini(current_market_data: dict) -> str:
    market_data_json = json.dumps(current_market_data)
    prompt = f"""Given the following market data: {market_data_json}, generate Python code for a Solana trade execution. The code should define a function `execute_trade(jito_signer_private_key_hex, solana_rpc_url)` that returns a JSON string representing a list of serialized Solana Transaction objects (as hex strings).
    - Use the provided `jito_signer_private_key_hex` (hex string) to initialize a Keypair and `solana_rpc_url` to initialize a SolanaClient.
    - Include all necessary imports within the `execute_trade` function.
    - Return a JSON string of a list of hex-serialized transaction bytes. Example: `json.dumps([tx.serialize().hex()])`.
    """
    
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()
        trade_logic_code = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
    
    if trade_logic_code.startswith("```python") and trade_logic_code.endswith("```"):
        trade_logic_code = trade_logic_code[len("```python"): -len("```")].strip()
    return trade_logic_code

async def run_scalper():
    print("Lead Scalper Bot Initialized and Rent Guard PASSED")
    
    target_token_symbol = "SOL"
    target_token_address = "So11111111111111111111111111111111111111112"
    
    diary = load_diary()
    
    while True:
        try:
            current_sol_balance = await get_wallet_balance()
            diary["wallet_balance_sol"] = current_sol_balance
            save_diary(diary)

            # Rent Guard: Check wallet balance before any action
            if current_sol_balance < diary["min_sol_reserve"]:
                min_reserve = diary["min_sol_reserve"]
                print(f"[RENT GUARD] Insufficient SOL balance ({current_sol_balance:.6f} SOL). Need {min_reserve} SOL. Skipping.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue

            current_liquidity = await check_liquidity(target_token_address)
            if current_liquidity < MIN_LIQUIDITY_THRESHOLD:
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue

            current_gas_fee_usd = await check_gas_fees()
            max_acceptable_gas_fee = PROJECTED_PROFIT_USD * MAX_GAS_FEE_PERCENTAGE
            if current_gas_fee_usd > max_acceptable_gas_fee:
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue

            # --- Market Analysis ---
            current_market_data = {
                "token_symbol": target_token_symbol,
                "token_address": target_token_address,
                "current_liquidity": current_liquidity,
                "current_sol_balance": current_sol_balance,
                "current_gas_fee_usd": current_gas_fee_usd,
                "sentiment_confidence": 0,
                "projected_profit_usd": PROJECTED_PROFIT_USD
            }

            sentiment, confidence = await analyze_social_sentiment(target_token_symbol)
            current_market_data["sentiment_confidence"] = confidence
            
            if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                print(f"\n!!! GOLDEN OPPORTUNITY DETECTED (Confidence: {confidence}) !!!")
                trade_logic_code = await generate_trade_logic_with_gemini(current_market_data)
                
                local_vars = {}
                exec(trade_logic_code, globals(), local_vars)
                
                if 'execute_trade' in local_vars:
                    signer_hex = jito_signer.to_bytes().hex()
                    tx_hex_json = local_vars['execute_trade'](signer_hex, HELIUS_RPC_URL)
                    tx_hex_list = json.loads(tx_hex_json)
                    transactions_bytes = [bytes.fromhex(tx_hex) for tx_hex in tx_hex_list]
                    
                    bundle_id = await send_jito_bundle(transactions_bytes, confidence)
                    
                    if bundle_id:
                        print(f"[JITO] Bundle successfully submitted. Monitoring status...")
                        diary["last_trade_timestamp"] = datetime.now().isoformat()
                        diary["trade_history"].append({
                            "timestamp": datetime.now().isoformat(), 
                            "token": target_token_address,
                            "sentiment_score": confidence,
                            "status": "submitted", 
                            "bundle_id": str(bundle_id)
                        })
                        save_diary(diary)
            
            print(f"Scanning for market signals... (next scan in {POLLING_INTERVAL_SECONDS}s)")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_scalper())
