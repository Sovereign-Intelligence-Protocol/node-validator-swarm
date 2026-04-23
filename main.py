# Aggressive Sniper Swarm - Final Migration
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

# --- THE PLUG-AND-PLAY SETUP ---
MY_API_KEY = "AIzaSyCjVh_3Zi_90ljhgXsNNO_V9relgNrpICo"
client = genai.Client(api_key=MY_API_KEY)

# Pulling Solana/Helius keys from Render Environment Variables
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

# --- Swarm Intelligence Logic ---
async def call_rpc(method, params):
    async with httpx.AsyncClient() as h_client:
        try:
            response = await h_client.post(HELIUS_RPC_URL, json={"jsonrpc":"2.0","id":1,"method":method,"params":params})
            return response.json()
        except:
            return None

async def analyze_sentiment(query):
    try:
        prompt = f"Analyze '{query}' for crypto
