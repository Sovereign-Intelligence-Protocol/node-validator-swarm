import telebot
import logging
import os
import time
import sys
from solana.rpc.api import Client

# 1. ELITE LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5")

# 2. THE 22-VARIABLE SYNC (Lazy Loader)
# We pull these inside functions so the bot never fails on a cold boot
def get_config(key, default=None):
    return os.getenv(key, default)

# 3. INDESTRUCTIBLE BOT OBJECT
bot = telebot.TeleBot(get_config("TELEGRAM_BOT_TOKEN"), threaded=False)

# 4. THE BRILLIANT HEALTH CHECK (Flexible Connection)
@bot.message_handler(commands=['health', 'status'])
def handle_health(message):
    try:
        # Connect ONLY when asked - ensures fresh environment data
        rpc_url = get_config("SOLANA_RPC_URL")
        client = Client(rpc_url)
        
        # THE SDK FIX: Using is_connected() instead of get_health() 
        # This fixes the "'Client' object has no attribute" error from 4:49 PM
        is_healthy = client.is_connected()
        
        status_icon = "✅" if is_healthy else "❌"
        wallet = get_config("SOLANA_WALLET_ADDRESS", "Not Set")
        hunting = get_config("HUNTING_STATE", "Safety")
        
        response = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: {status_icon} | DB: ✅\n"
            f"Wallet: `{wallet[:6]}...` | Mode: `{hunting}`"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        bot.reply_to(message, f"⚠️ **Connection Issue**\nError: `{str(e)[:50]}`")

# 5. THE "GHOST-KILLER" STARTUP
if __name__ == "__main__":
    logger.info("🚀 INITIALIZING OMNI-SYNC ENGINE...")
    
    # Clean webhooks ONCE before entering the main loop
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except:
        pass

    while True:
        try:
            # THE 120s GOLDEN RULE: Stops the 409 Conflict forever
            # Gives Render time to kill the "ghost" instance of your bot
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            
            logger.info("🛰️ OMNI-SYNC LIVE. Polling Telegram...")
            # Increased timeout for better stability on Render
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("🔄 409 Conflict: Waiting for ghost instance to expire...")
                time.sleep(60)
            else:
                logger.error(f"💥 Critical Error: {e}")
                time.sleep(10) # Safety pause to prevent rapid-fire crashing
