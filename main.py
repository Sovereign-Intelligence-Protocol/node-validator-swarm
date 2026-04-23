# Lead Scalper Bot - Unified Production Code
# Refactored for google-genai SDK (Gemini 2.0 Flash)
import os
import time
import asyncio
import json
import re
import base58
import httpx
from datetime import datetime
from dotenv import load_dotenv

# SDK Imports
from google import genai
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey as PublicKey
from solders.keypair import Keypair as SoldersKeypair

# Load environment variables
load_dotenv()

# --- Configuration & Environment Check ---
# The SDK automatically uses GOOGLE_API_KEY or GEMINI_API_KEY from your environment
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY") or os.getenv("I_KEY")
SOLANA_RPC_URL_BASE = os.getenv("SOLANA_RPC_URL_BASE") or os.getenv("HELIUS_RPC_URL") or os.getenv("RPC_URL")
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")
JITO_BLOCK_ENGINE_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"

# Initialize the new Google GenAI Client
client = genai.Client()

# Check for required variables to prevent crashes on Render
missing_vars = []
if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")): missing_vars.append("GOOGLE_API_KEY")
if not HELIUS_API_KEY: missing_vars.append("HELIUS_API_KEY")
if not SOLANA_RPC_URL_BASE: missing_vars.append("SOLANA_RPC_URL_BASE")
if not JITO_SIGNER_PRIVATE_KEY: missing_vars.append("JITO_SIGNER_PRIVATE_KEY")

if missing_vars:
    print(f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_vars)}")
    exit(1)

# RPC Setup
HELIUS_RPC_URL = f"{SOLANA_RPC_URL_BASE}/?api-key={HELIUS_API_KEY}"
solana_client = SolanaClient(HELIUS_RPC_URL)

# Signer Initialization
jito_signer = None
try:
    raw_key = JITO_SIGNER_PRIVATE_KEY.strip().strip("'").strip('"')
    if raw_key.startswith("["):
        key_list = json.loads(raw_key)
        jito_signer = SoldersKeypair.from_bytes(bytes(key_list))
    else:
        key_bytes = base58.b58decode(raw_key)
        jito_signer = SoldersKeypair.from_bytes(key_bytes) if len(key_bytes) != 32 else SoldersKeypair.from_seed(key_bytes)
    print(f"[SIGNER] Initialized: {jito_signer.pubkey()}")
except Exception as e:
    print(f"CRITICAL ERROR: Signer failed: {e}")
    exit(1)

# --- Trading Parameters ---
MIN_LIQUIDITY_THRESHOLD = 250000
MIN_GEMINI_CONFIDENCE_SCORE = 85
POLLING_INTERVAL_SECONDS = 2
MIN_SOL_RESERVE = 0.02
PROJECTED_PROFIT_USD = 5
MAX_GAS_FEE_PERCENTAGE = 0.20
MAX_JITO_TIP_SOL = 0.0005
SENTIMENT_CACHE_TTL = 300
sentiment_cache = {}

# --- RPC Helpers ---
async def call_helius_rpc(method: str, params: list) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient() as h_client:
        response = await h_client.post(HELIUS_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_wallet_balance() -> float:
    try:
        result = await call_helius_rpc("getBalance", [str(jito_signer.pubkey())])
        return result["result"]["value"] / 1e9
    except:
        return 0.0

# --- Core AI Logic (Gemini 2.0 Flash) ---
async def analyze_social_sentiment(query: str) -> tuple:
    current_time = time.time()
    if query in sentiment_cache and (current_time - sentiment_cache[query]["timestamp"] < SENTIMENT_CACHE_TTL):
        return sentiment_cache[query]["sentiment"], sentiment_cache[query]["confidence"]

    try:
        prompt = f"Analyze '{query}' for crypto sentiment and rug risk. Format: Sentiment: [positive/neutral/negative], Confidence: [1-100], Risk: [0-100%]"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = response.text.lower()
        
        sentiment = "positive" if "positive" in text else "negative" if "negative" in text else "neutral"
        conf_match = re.search(r"confidence:\s*(\d+)", text)
        risk_match = re.search(r"risk:\s*(\d+)", text)
        
        confidence = int(conf_match.group(1)) if conf_match else 0
        risk = int(risk_match.group(1)) if risk_match else 100
        
        if risk > 15: confidence = 0 # Safety filter

        sentiment_cache[query] = {"sentiment": sentiment, "confidence": confidence, "timestamp": current_time}
        return sentiment, confidence
    except:
        return "neutral", 0

async def generate_trade_logic(market_data: dict) -> str:
    try:
        prompt = f"Create Solana trade code for: {json.dumps(market_data)}. Define execute_trade(signer_hex, rpc_url) returning hex tx list JSON."
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        code = response.text.strip()
        return code.split("```python")[-1].split("```")[0].strip() if "```" in code else code
    except:
        return ""

async def send_jito_bundle(transactions: list):
    try:
        import base64
        tx_list = [base64.b64encode(tx).decode('utf-8') for tx in transactions]
        payload = {"jsonrpc": "2.0", "id": 1, "method": "sendBundle", "params": [tx_list]}
        async with httpx.AsyncClient(timeout=10.0) as h_client:
            await h_client.post(JITO_BLOCK_ENGINE_URL, json=payload)
    except:
        pass

# --- Execution Loop ---
async def main_loop():
    print("HARD-CONNECT Elite Edition ACTIVE")
    while True:
        try:
            balance = await get_wallet_balance()
            if balance >= MIN_SOL_RESERVE:
                sentiment, confidence = await analyze_social_sentiment("SOL")
                if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                    print(f"!!! OPPORTUNITY DETECTED ({confidence}%) !!!")
                    market_data = {"balance": balance, "liquidity": 500000, "confidence": confidence}
                    code = await generate_trade_logic(market_data)
                    
                    if code:
                        local_vars = {}
                        exec(code, globals(), local_vars)
                        if 'execute_trade' in local_vars:
                            tx_json = local_vars['execute_trade'](jito_signer.to_bytes().hex(), HELIUS_RPC_URL)
                            await send_jito_bundle([bytes.fromhex(tx) for tx in json.loads(tx_json)])
            else:
                print(f"[RENT GUARD] Balance low: {balance:.4f} SOL")

            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main_loop())
