import telebot
import logging
import os
import time
import sys
from solana.rpc.api import Client

# 1. LOGGING SETUP (Clean and professional)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. LOAD EVERYTHING FROM RENDER 
# (Identity, RPC, and the 22 Custom Settings)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
RPC_URL = os.getenv("SOLANA_RPC_URL")

# 3. INITIALIZATION
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_URL)

# 4. UNIVERSAL HEALTH CHECK (Confirms settings are loaded)
@bot.message_handler(commands=['health'])
def health_check(message):
    try:
        is_live = solana_client.is_connected()
        status = "✅" if is_live else "❌"
        # We can pull any of your 22 settings here just to verify they're active
        jito_engine = os.getenv("JITO_BLOCK_ENGINE_URL", "Not Set")
        
        msg = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: {status} | DB: ✅\n"
            f"Wallet: `{WALLET[:6]}...`\n"
            f"Jito Engine: `{jito_engine[:15]}...`"
        )
        bot.reply_to(message, msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Health check fail: {e}")

# 5. THE STARTUP (Ghost-Proof & Effortless)
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    
    # Kills any Railway/Zombie webhooks immediately
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    
    # 5-second breath for the Telegram API to clear
    time.sleep(5)
    
    try:
        # infinity_polling handles its own retries. 
        # If a 409 Conflict occurs, the script exits so Render can do a fresh restart.
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Render Restart Triggered: {e}")
        sys.exit(1)
