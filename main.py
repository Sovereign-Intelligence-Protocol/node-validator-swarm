import os
import logging
import asyncio
import base58
import redis
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

# --- 1. LOGGING SETUP ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. ENVIRONMENT VARIABLES (With Safety Defaults) ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
RPC_URL = os.getenv("RPC_URL", "")
WALLET_ADDR = os.getenv("SOLANA_WALLET_ADDRESS", "")
PRIV_KEY_STR = os.getenv("SOLANA_PRIVATE_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "")

# --- 3. CORE LOGIC FUNCTIONS ---

async def get_on_chain_balance():
    # Shield: Prevent 'NoneType' error if variables aren't loaded
    if not RPC_URL or not WALLET_ADDR:
        return "CONFIG_MISSING"
    try:
        async with AsyncClient(RPC_URL) as client:
            pubkey = Pubkey.from_string(WALLET_ADDR)
            res = await client.get_balance(pubkey)
            # Shield: Safely check for 'value' before subscripting or dividing
            if res and hasattr(res, 'value'):
                return res.value / 1_000_000_000
            return 0.0
    except Exception as e:
        logger.error(f"Balance Check Failed: {e}")
        return "RPC_ERROR"

# --- 4. COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🚀 **S.I.P. Mainnet Dashboard**\n\n"
        f"📍 **Bridge Wallet:** `{WALLET_ADDR[:6]}...{WALLET_ADDR[-4:]}`\n"
        "🏛️ **Destination:** Kraken Account\n"
        "🛰️ **Status:** Monitoring Solana Mainnet..."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ **Initiating Sovereign Audit...**")
    
    # Run the balance check
    balance = await get_on_chain_balance()
    rpc_status = "✅ ONLINE" if isinstance(balance, float) else f"❌ {balance}"
    
    # Check Signer (The Private Key Logic)
    signer_status = "❌ NOT FOUND"
    if PRIV_KEY_STR:
        try:
            # Shield: Validates the string without crashing the
