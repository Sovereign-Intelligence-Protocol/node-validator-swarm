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

# --- 2. ENVIRONMENT VARIABLES ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RPC_URL = os.getenv("RPC_URL")
WALLET_ADDR = os.getenv("SOLANA_WALLET_ADDRESS")
PRIV_KEY_STR = os.getenv("SOLANA_PRIVATE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

# --- 3. CORE LOGIC FUNCTIONS ---

async def get_on_chain_balance():
    if not RPC_URL or not WALLET_ADDR:
        return "Config Missing"
    try:
        async with AsyncClient(RPC_URL) as client:
            pubkey = Pubkey.from_string(WALLET_ADDR)
            res = await client.get_balance(pubkey)
            if res and hasattr(res, 'value'):
                return res.value / 1_000_000_000
            return 0
    except Exception as e:
        logger.error(f"Balance Check Failed: {e}")
        return "Error"

# --- 4. COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🚀 **S.I.P. Mainnet Dashboard**\n\n"
        f"📍 **Bridge Wallet:** `{WALLET_ADDR[:6]}...{WALLET_ADDR[-4:]}`\n"
        "🏛️ **Destination:** Kraken Account\n"
        "🛰️ **Status:** Polling Solana Mainnet..."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ **Initiating Sovereign Audit...**")
    
    # Check RPC/Balance
    balance = await get_on_chain_balance()
    rpc_status = "✅ ONLINE" if isinstance(balance, float) else "❌ DISCONNECTED"
    
    # Check Signer (The Private Key Logic)
    signer_status = "❌ NOT FOUND"
    if PRIV_KEY_STR:
        try:
            # Decoding the Base58 string you confirmed (DfFB...)
            Keypair.from_bytes(base58.b58decode(PRIV_KEY_STR))
            signer_status = "✅ ARMED"
        except Exception as e:
            signer_status = f"❌ FORMAT ERROR: {str(e)[:15]}"

    # Check Redis
    db_status = "❌ OFFLINE"
    if REDIS_URL:
        try:
            r = redis.from_url(REDIS_URL)
            if r.ping(): db_status = "✅ CONNECTED"
        except: pass

    report = (
        "📊 **SYSTEM AUDIT REPORT**\n"
        "--- --- --- --- ---\n"
        f"🌐 **RPC Node:** {rpc_status}\n"
        f"🔑 **Signer/Key:** {signer_status}\n"
        f"🗄️ **Database:** {db_status}\n"
        f"💰 **Balance:** `{balance}` SOL\n"
        "--- --- --- --- ---\n"
        "🟢 **Status:** *Operational*" if "✅" in signer_status else "🔴 **Status:** *Attention Required*"
    )
    await update.message.reply_text(report, parse_mode='Markdown')

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await get_on_chain_balance()
    await update.message.reply_text(f"💰 **Current Bridge Balance:** `{bal}` SOL", parse_mode='Markdown')

async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📡 **Lead Scalper:** Searching liquidity pairs... (Check Render Logs for output)")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **S.I.P. Protocol Commands**\n"
        "/start - Dashboard\n"
        "/health - System Audit\n"
        "/balance - Check SOL\n"
        "/scrape - Hunt leads"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# --- 5. MAIN EXECUTION ---

def main():
    if not TOKEN:
        print("CRITICAL ERROR: TELEGRAM_BOT_TOKEN is missing!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # Registering handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("balance", balance_cmd))
    application.add_handler(CommandHandler("scrape", scrape))
    application.add_handler(CommandHandler("help", help_cmd))

    print("--- Sovereign Protocol Online ---")
    application.run_polling()

if __name__ == "__main__":
    main()
