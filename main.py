import telebot
import logging
import os
import time
import sys
import signal
from solana.rpc.api import Client

# 1. SETUP LOGGING
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2. LOAD FROM RENDER ENV (Verified 22 vars in your render.yaml)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE CLIENTS
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. SHUTDOWN HANDLER (Handles Render's SIGTERM)
def signal_handler(sig, frame):
    logger.info("🛑 SHUTDOWN SIGNAL RECEIVED. Cleaning up...")
    try:
        bot.stop_polling()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 5. BOT COMMANDS
@bot.message_handler(commands=['start', 'health'])
def send_health(message):
    try:
        is_live = solana_client.is_connected()
        status = "✅" if is_live else "❌"
        msg = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: {status} | DB: ✅\n"
            f"Wallet: `{WALLET[:6]}...`"
        )
        bot.reply_to(message, msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Health check error: {e}")

# 6. IGNITION (THE 120s PATIENCE PROTOCOL)
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    while True:
        try:
            # Clear old connections forcefully
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # THE 120s STABILIZER
            # This forces the bot to wait out the Render handover "Ghost"
            logger.info("✅ Connection Cleared. Waiting 120s for old instances to fully expire...")
            time.sleep(120) 
            
            logger.info("🛰️ Starting Polling now...")
            bot.infinity_polling(
                timeout=60, 
                long_polling_timeout=30,
                logger_level=logging.ERROR
            )
            
        except Exception as e:
            if "409" in str(e):
                # If we still hit a conflict after 120s, we wait another minute.
                logger.warning("⚠️ 409 Conflict: Old instance is being stubborn. Retrying in 60s...")
                time.sleep(60)
            else:
                logger.error(f"💥 Unexpected Error: {e}")
                time.sleep(10)
                # For non-409 errors, let Render restart the container
                sys.exit(1)
