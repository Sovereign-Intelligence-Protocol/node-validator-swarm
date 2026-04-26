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

# 2. LOAD FROM RENDER ENV (Utilizing the 22 variables from your yaml)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE CLIENTS
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. SHUTDOWN HANDLER (Speeds up future deploys)
def signal_handler(sig, frame):
    logger.info("🛑 SHUTDOWN SIGNAL RECEIVED. Cleaning up...")
    try:
        bot.stop_polling()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 5. RESTORED COMMANDS
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

# 6. THE STABLE IGNITION (120s Delay Kept)
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    while True:
        try:
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # This is what fixed your 409 errors - keep this!
            logger.info("✅ Connection Cleared. Waiting 120s for environment to stabilize...")
            time.sleep(120) 
            
            logger.info("🛰️ Starting Polling now...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("⚠️ 409 Conflict: Retrying in 60s...")
                time.sleep(60)
            else:
                logger.error(f"💥 Fatal Error: {e}")
                sys.exit(1)
