import telebot
import logging
import os
import time
import sys
from solana.rpc.api import Client

# 1. SETUP LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. LOAD FROM RENDER ENV
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZE
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. HEALTH CHECK
@bot.message_handler(commands=['health'])
def health(message):
    is_live = solana_client.is_connected()
    bot.reply_to(message, f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\nRPC: {'✅' if is_live else '❌'}\nWallet: `{WALLET[:6]}...`", parse_mode="Markdown")

# 5. THE RESILIENT STARTUP
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    # We loop here specifically to handle the "Render Handover" 409 error
    while True:
        try:
            # Kill any lingering webhooks
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            logger.info("✅ Connection Cleared. Starting Polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("⚠️ 409 Conflict: Old instance still active. Retrying in 10s...")
                time.sleep(10)
            else:
                logger.error(f"💥 Unexpected Error: {e}")
                time.sleep(5)
                # If it's not a 409, let Render restart the whole container
                sys.exit(1)
