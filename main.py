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

# --- 1. LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. ENVIRONMENT VARIABLES ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
RPC_URL = os.getenv("RPC_URL", "")
WALLET_ADDR = os.getenv("SOLANA_WALLET_ADDRESS", "")
PRIV_KEY_STR = os.getenv("SOLANA_PRIVATE_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "")

# --- 3. CORE LOGIC ---
async def get_on_chain_balance():
    if not RPC_URL or not WALLET_ADDR:
        return "CONFIG_MISSING"
    try:
        async with AsyncClient(RPC_URL) as client:
            pubkey = Pubkey.from_string(WALLET_ADDR)
            res = await client.get_balance(pubkey)
            if res is not None and hasattr(res, 'value'):
                return res.value / 1_000_000_000
            return 0.0
    except Exception as e:
        logger.error(f"Balance error: {e}")
        return "ERROR"

# --- 4. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **S.I.P. Protocol Online.** Use /health for audit.")

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ **Auditing Systems...**")
    balance = await get_on_chain_balance()
    signer_status = "❌ NOT FOUND"
    if PRIV_KEY_STR:
        try:
            Keypair.from_bytes(base58.b58decode(PRIV_KEY_STR))
            signer_status = "✅ ARMED"
        except:
            signer_status = "❌ FORMAT ERROR"
    
    report = (
        "📊 **SYSTEM AUDIT**\n"
        f"🌐 **RPC:** {'✅' if balance != 'ERROR' else '❌'}\n"
        f"🔑 **Signer:** {signer_status}\n"
        f"💰 **Balance:** `{balance}` SOL"
    )
    await update.message.reply_text(report, parse_mode='Markdown')

# --- 5. MAIN ---
def main():
    if not TOKEN:
        logger.error("No Token Found")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health_check))
    logger.info("--- Sovereign Protocol Online ---")
    app.run_polling()

if __name__ == "__main__":
    main()
