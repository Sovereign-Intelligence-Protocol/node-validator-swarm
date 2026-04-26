import telebot
import logging
import os
import time
import sys
import signal
from solana.rpc.api import Client

# 1. SETUP LOGGING
# High-visibility logging to track the 120s timer in Render Live Tail
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2. LOAD FROM RENDER ENV
# These match the keys verified in your render.yaml
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE CLIENTS
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. SHUTDOWN HANDLER
# Ensures the bot stops polling gracefully when Render rotates instances
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
# Re-adding the status check so you can verify the connection via Telegram
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
# This handles the 409 Conflict seen in your logs by out-waiting the old instance
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    while True:
        try:
            # Forcefully clear any lingering webhooks or sessions
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # THE 120s STABILIZER
            # Essential to prevent the 409 error during Render handovers
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
                # Back-off logic if Render is still holding the old instance
                logger.warning("⚠️ 409 Conflict: Old instance still active. Retrying in 60s...")
                time.sleep(60)
            else:
                logger.error(f"💥 Unexpected Error: {e}")
                time.sleep(10)
                sys.exit(1)
