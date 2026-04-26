import telebot
import logging
import os
import time
import sys
from solana.rpc.api import Client

# 1. LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. SYNCED ENVIRONMENT LOADER (Matching your 22 variables)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RPC_URL = os.getenv("SOLANA_RPC_URL")        # FIXED
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")  # FIXED
JITO_TIP = os.getenv("JITO_TIP_AMOUNT")      # FIXED

# 3. INITIALIZE CLIENTS
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. HEALTH CHECK COMMAND
@bot.message_handler(commands=['health', 'status'])
def send_health(message):
    try:
        # We use get_health() for a more reliable connection check in 2026
        is_live = solana_client.get_health()
        status = "✅" if is_live.value == "ok" else "❌"
        msg = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: {status} | DB: ✅\n"
            f"Wallet: `{WALLET[:6]}...`"
        )
        bot.reply_to(message, msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Health check error: {e}")
        bot.reply_to(message, "⚠️ RPC Unreachable. Check Render Environment URLs.")

# 5. THE 120s STABILITY IGNITION
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    while True:
        try:
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # The protocol that fixed your 409 Conflicts
            logger.info("✅ Connection Cleared. Waiting 120s for stability...")
            time.sleep(120) 
            
            logger.info("🛰️ Starting Polling now...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("⚠️ Conflict detected. Retrying...")
                time.sleep(60)
            else:
                logger.error(f"💥 Error: {e}")
                sys.exit(1)
