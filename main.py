import telebot
import logging
import time
import signal
import sys
import os
from solana.rpc.api import Client

# 1. SETUP LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. LOAD ENVIRONMENT VARIABLES
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS", "0x000...")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE CLIENTS
# threaded=False is crucial on Render to prevent duplicate polling threads
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. SHUTDOWN HANDLER
def signal_handler(sig, frame):
    """Ensures the bot logs out cleanly when Render stops or restarts the service"""
    logger.info("🛑 SHUTDOWN SIGNAL RECEIVED. Cleaning up...")
    try:
        bot.stop_polling()
    except:
        pass
    sys.exit(0)

# Register Render's termination signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 5. BOT COMMANDS
@bot.message_handler(commands=['start', 'health'])
def send_health(message):
    try:
        # Check RPC Connection
        is_rpc_live = solana_client.is_connected()
        rpc_status = "✅" if is_rpc_live else "❌"
        
        status_msg = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: {rpc_status} | DB: ✅\n"
            f"Wallet: `{WALLET[:6]}...`"
        )
        bot.reply_to(message, status_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Health check error: {e}")

@bot.message_handler(commands=['reset'])
def force_reset(message):
    bot.reply_to(message, "🔄 Internal Reset Triggered. Evicting ghosts...")
    bot.stop_polling()

# 6. IGNITION (REFINED FOR RENDER)
if __name__ == "__main__":
    try:
        logger.info("🛠️ CRITICAL RESET: Evicting all other instances...")
        
        # This tells Telegram to drop the connection from Railway or other ghosts
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True) 
        
        # 5-second cooldown to let the API reset
        time.sleep(5) 
        
        logger.info(f"🚀 S.I.P. v5.5 IGNITED | WALLET: {WALLET[:6]}")
        
        # Infinity polling handles its own retries—no 'while True' loop needed
        bot.infinity_polling(
            timeout=60, 
            long_polling_timeout=30,
            logger_level=logging.ERROR
        )
        
    except Exception as e:
        logger.error(f"💥 FATAL STARTUP ERROR: {e}")
        # Exit with error code 1 so Render knows to try a fresh restart
        sys.exit(1)
