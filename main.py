import telebot
import logging
import os
import time
import sys
import signal
from solana.rpc.api import Client

# 1. SETUP LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. LOAD FROM RENDER ENV
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE
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

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 5. THE RESILIENT STARTUP
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    while True:
        try:
            # Clear old connections
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # INCREASED WAIT: 30 seconds to force a full session reset
            logger.info("✅ Connection Cleared. Waiting 30s for environment to stabilize...")
            time.sleep(30) 
            
            logger.info("🛰️ Starting Polling now...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("⚠️ Still hitting a 409. Retrying in 30s...")
                time.sleep(30)
            else:
                logger.error(f"💥 Fatal Error: {e}")
                sys.exit(1)
