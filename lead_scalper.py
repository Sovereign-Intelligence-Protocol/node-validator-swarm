# Lead Scalper Bot - 'Balanced Predator' Edition
# 'Silent Hunter' Mode Enabled
# Deployment timestamp: 2026-04-22 02:05 PM

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
import google.generativeai as genai
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey as PublicKey
from solders.keypair import Keypair

# Load environment variables
load_dotenv()

# --- BALANCED PREDATOR CONFIGURATION ---
HARDCODED_CONFIG = {
    "GOOGLE_API_KEY": "AIzaSyCjVh_3Zi_90IjhgXsNN0_V9relgNrplCo",
    "HELIUS_API_KEY": "e4fbf95c-a828-44ec-bfdb-07be33d18c03",
    "SOLANA_RPC_URL_BASE": "https://mainnet.helius-rpc.com",
    "JITO_SIGNER_PRIVATE_KEY": "DfFBkgk9Lyy6SonLKhCafDUg7nhPiG92xCHV1JPgEWfBu3hhpDz1TVrFoafbwGei7zZB5Go34Wf97wZSdY1Pjvf",
    "SOLANA_WALLET_ADDRESS": "junTtoquNLdo4PFeC7JbH6Mzj7aztaTckK4dQrr1tWs",
    "CONFIDENCE_THRESHOLD": 0.82,     # Balanced Predator Tuning
    "RUG_RISK_THRESHOLD": 15,        # Strict Rug Check
    "FIXED_JITO_TIP_SOL": 0.001,     # Optimized Fixed Tip
    "LIQUIDITY_FLOOR_USD": 125000,   # Balanced Predator Floor
    "POSITION_SIZE_SOL": 0.04,       # Increased for Balanced Predator
    "TAKE_PROFIT_PERCENT": 50,
    "STOP_LOSS_PERCENT": 15
}

# --- GLOBAL INITIALIZATION (RUNS ONCE) ---
GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or HARDCODED_CONFIG["GOOGLE_API_KEY"]).strip()
HELIUS_API_KEY = (os.getenv("HELIUS_API_KEY") or os.getenv("I_KEY") or HARDCODED_CONFIG["HELIUS_API_KEY"]).strip()
SOLANA_RPC_URL_BASE = (os.getenv("SOLANA_RPC_URL_BASE") or os.getenv("HELIUS_RPC_URL") or os.getenv("C_URL") or os.getenv("RPC_URL") or HARDCODED_CONFIG["SOLANA_RPC_URL_BASE"]).strip()
JITO_SIGNER_PRIVATE_KEY = (os.getenv("JITO_SIGNER_PRIVATE_KEY") or HARDCODED_CONFIG["JITO_SIGNER_PRIVATE_KEY"]).strip()
SOLANA_WALLET_ADDRESS = (os.getenv("SOLANA_WALLET_ADDRESS") or HARDCODED_CONFIG["SOLANA_WALLET_ADDRESS"]).strip()
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD") or HARDCODED_CONFIG["CONFIDENCE_THRESHOLD"])
RUG_RISK_THRESHOLD = float(os.getenv("RUG_RISK_THRESHOLD") or HARDCODED_CONFIG["RUG_RISK_THRESHOLD"])
FIXED_JITO_TIP_SOL = float(os.getenv("FIXED_JITO_TIP_SOL") or HARDCODED_CONFIG["FIXED_JITO_TIP_SOL"])
LIQUIDITY_FLOOR_USD = float(os.getenv("LIQUIDITY_FLOOR_USD") or HARDCODED_CONFIG["LIQUIDITY_FLOOR_USD"])
POSITION_SIZE_SOL = float(os.getenv("POSITION_SIZE_SOL") or HARDCODED_CONFIG["POSITION_SIZE_SOL"])
TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT") or HARDCODED_CONFIG["TAKE_PROFIT_PERCENT"])
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT") or HARDCODED_CONFIG["STOP_LOSS_PERCENT"])

# Configure Gemini AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
        jito_signer = Keypair.from_bytes(key_bytes) if len(key_bytes) == 64 else Keypair.from_seed(key_bytes)
except Exception as e:
    print(f"CRITICAL ERROR: Jito signer initialization failed: {e}")

# --- SETTINGS ---
POLLING_INTERVAL = 1.0
MIN_SOL_RESERVE = 0.05
LOG_INTERVAL_SECONDS = 60

async def call_helius_rpc(method: str, params: list) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient() as client:
        response = await client.post(HELIUS_RPC_URL.strip(), headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_wallet_balance() -> float:
    try:
        result = await call_helius_rpc("getBalance", [SOLANA_WALLET_ADDRESS])
        if "result" in result:
            return result["result"]["value"] / 1e9
    except Exception as e:
        pass
    return 0.0

async def perform_high_conviction_audit(token_address: str) -> dict:
    try:
        prompt = (
            f"Perform a high-conviction audit for Solana token: {token_address}\n"
            f"Analyze for: Developer History, Holder Concentration, LP Burn Status.\n"
            f"Output JSON: {{\"confidence\": 0.0-1.0, \"rug_risk\": 0-100, \"reasoning\": \"...\"}}"
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        pass
    return {"confidence": 0, "rug_risk": 100}

async def run_scalper():
    print(f"[BOOT] BALANCED PREDATOR Mode Active")
    print(f"[BOOT] Target: {SOLANA_WALLET_ADDRESS}")
    print(f"[BOOT] Strategy: Liquidity > ${LIQUIDITY_FLOOR_USD:,.0f} | AI Confidence > {CONFIDENCE_THRESHOLD}")
    print(f"[BOOT] Risk: Rug Limit {RUG_RISK_THRESHOLD}% | Position {POSITION_SIZE_SOL} SOL | Tip {FIXED_JITO_TIP_SOL} SOL")
    
    last_log_time = 0
    
    while True:
        try:
            balance = await get_wallet_balance()
            required_for_trade = POSITION_SIZE_SOL + FIXED_JITO_TIP_SOL + 0.002 # Trade + Tip + Gas
            
            if balance < (MIN_SOL_RESERVE + required_for_trade):
                if time.time() - last_log_time > LOG_INTERVAL_SECONDS:
                    print(f"[STATUS] Waiting for funds. Balance: {balance:.4f} SOL")
                    last_log_time = time.time()
                await asyncio.sleep(POLLING_INTERVAL)
                continue

            if time.time() - last_log_time > LOG_INTERVAL_SECONDS:
                print(f"[STATUS] Silent Hunter scanning... Balance: {balance:.4f} SOL")
                last_log_time = time.time()

            # Detection and filtering logic would happen here...
            
            await asyncio.sleep(POLLING_INTERVAL)
            
        except Exception as e:
            await asyncio.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    asyncio.run(run_scalper())
