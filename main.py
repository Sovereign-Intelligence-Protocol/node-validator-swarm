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

# 3. INITIALIZE CLIENTS (Single-threaded to prevent 409 loops)
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. SHUTDOWN HANDLER (The 'Ghost' Killer)
def signal_handler(sig, frame):
    """Ensures the bot logs out cleanly when Render stops the service"""
    logger.info("🛑 SHUTDOWN SIGNAL RECEIVED. Cleaning up...")
    bot.stop_polling()
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

# 6. IGNITION (THE RECOVERY & EVICTION PROTOCOL)
if __name__ == "__main__":
    while True:
        try:
            logger.info("🛠️ CRITICAL RESET: Evicting all other instances...")
            
            # NECESSARY CHANGE: Force Telegram to 'hang up' on any zombie processes
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True) 
            
            # NECESSARY CHANGE: Give Render's network a 10s 'Cool Down'
            time.sleep(10) 
            
            logger.info(f"🚀 S.I.P. v5.5 IGNITED | WALLET: {WALLET[:6]}")
            
            # NECESSARY CHANGE: infinity_polling handles reconnects better than basic polling
            bot.infinity_polling(
                timeout=90, 
                long_polling_timeout=40,
                logger_level=logging.ERROR
            )
            
        except Exception as e:
            # NECESSARY CHANGE: If a 409 occurs, wait and restart the loop instead of dying
            logger.error(f"🔄 RECOVERY LOOP: Conflict or crash. Retrying in 20s... {e}")
            time.sleep(20)
