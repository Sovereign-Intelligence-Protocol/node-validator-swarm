import os
import asyncio
import logging
import redis.asyncio as redis
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# 1. LOGGING SETUP
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. CONFIGURATION - FIXED TO FIND YOUR TOKEN AUTOMATICALLY
# This looks for any common name you might have used in Render
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TOKEN")
RPC_URL = os.getenv("RPC_URL")
WALLET_ADDR = os.getenv("SOLANA_WALLET_ADDRESS")
REDIS_URL = os.getenv("REDIS_URL", "")

# Auto-fix Redis prefix if needed
if REDIS_URL and not REDIS_URL.startswith("redis://"):
    REDIS_URL = f"redis://{REDIS_URL}"

# 3. CORE LOGIC
async def get_on_chain_balance():
    if not RPC_URL or not WALLET_ADDR:
        return "Config Missing"
    try:
        async with AsyncClient(RPC_URL) as client:
            pubkey = Pubkey.from_string(WALLET_ADDR)
            res = await client.get_balance(pubkey)
            return res.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance Error: {e}")
        return "Error"

# 4. COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance_sol = await get_on_chain_balance()
    dashboard = (
        "⚡ **SOVEREIGN PROTOCOL: ONLINE**\n\n"
        f"🏛️ **Destination:** Kraken\n"
        f"💳 **Wallet:** `{WALLET_ADDR[:6]}...{WALLET_ADDR[-4:]}`\n"
        f"⚖️ **Current Balance:** `{balance_sol}` SOL\n\n"
        "🟢 *Protocol Synchronized.*"
    )
    await update.message.reply_text(dashboard, parse_mode='Markdown')

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await get_on_chain_balance()
    await update.message.reply_text(f"⚖️ **Bridge Balance:** `{bal}` SOL")

async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 **S.I.P. ALERT:** Launching Lead Scalper...")
    try:
        import subprocess
        subprocess.Popen(["python3", "scraper.py"])
        await update.message.reply_text("✅ **Scraper Started.**")
    except Exception as e:
        await update.message.reply_text(f"❌ **Error:** {str(e)}")

# 5. MAIN EXECUTION
def main():
    if not TOKEN:
        logger.error("!!! NO TOKEN FOUND !!! Check your Render Environment Variables.")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_cmd))
    application.add_handler(CommandHandler("scrape", scrape))

    logger.info("Sovereign Protocol Online. Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
