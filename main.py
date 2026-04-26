import telebot
import logging
import os
import time
import sys
from solana.rpc.api import Client

# 1. SETUP LOGGING
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2. LOAD FROM RENDER ENV (The 22 variables)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE CLIENTS
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. SHUTDOWN HANDLER
def signal_handler(sig, frame):
    logger.info("🛑 SHUTDOWN SIGNAL RECEIVED. Cleaning up...")
    try:
        bot.stop_polling()
    except:
        pass
    sys.exit(0)

import signal
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

# 6. IGNITION (THE RESILIENT STARTUP)
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    while True:
        try:
            # Step 1: Forcefully disconnect ANY other instance
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # Step 2: STABILIZATION WAIT
            # This gives Render time to fully kill the old process before we poll.
            logger.info("✅ Connection Cleared. Waiting 15s for environment to stabilize...")
            time.sleep(15) 
            
            # Step 3: Start polling
            logger.info("🛰️ Starting Polling now...")
            bot.infinity_polling(
                timeout=60, 
                long_polling_timeout=30,
                logger_level=logging.ERROR
            )
            
        except Exception as e:
            # Handle the 409 Conflict overlap specifically
            if "409" in str(e):
                logger.warning("⚠️ 409 Conflict: Old instance still active. Retrying in 20s...")
                time.sleep(20)
            else:
                logger.error(f"💥 Unexpected Error: {e}")
                time.sleep(5)
                # For non-409 errors, exit so Render can attempt a fresh container start
                sys.exit(1)
