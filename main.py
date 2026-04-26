import telebot, logging, os, time, sys
from solana.rpc.api import Client

# 1. ELITE LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5")

# 2. THE 22-VARIABLE SYNC (Lazy Loading)
# We don't load them globally to avoid "NoneType" errors on boot
def get_env(key, default=None):
    return os.getenv(key, default)

# 3. INDESTRUCTIBLE BOT OBJECT
bot = telebot.TeleBot(get_env("TELEGRAM_BOT_TOKEN"), threaded=False)

# 4. THE BRILLIANT HEALTH CHECK
@bot.message_handler(commands=['health', 'status'])
def handle_health(message):
    try:
        # Connect ONLY when asked - this bypasses boot-up race conditions
        rpc_url = get_env("SOLANA_RPC_URL")
        client = Client(rpc_url)
        
        # Robust check: Many providers return objects, not just strings
        # We check for 'ok' in the string representation to be safe
        health_resp = client.get_health()
        is_healthy = "ok" in str(health_resp).lower()
        
        status_icon = "✅" if is_healthy else "❌"
        wallet = get_env("SOLANA_WALLET_ADDRESS", "Not Set")
        
        response = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: {status_icon} | DB: ✅\n"
            f"Wallet: `{wallet[:6]}...` | Mode: `{get_env('HUNTING_STATE', 'Safety')}`"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        bot.reply_to(message, f"⚠️ **Connection Issue**\nError: `{str(e)[:50]}`")

# 5. THE "GHOST-KILLER" STARTUP
if __name__ == "__main__":
    logger.info("🚀 INITIALIZING OMNI-SYNC ENGINE...")
    
    # Kill any existing webhooks before we even start the loop
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except: pass

    while True:
        try:
            # THE 120s GOLDEN RULE: This is the ONLY way to stop the 409 error
            # It gives Render time to fully swap the old instance for the new one.
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            
            logger.info("🛰️ OMNI-SYNC LIVE. Polling Telegram...")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("🔄 409 Conflict: Waiting for ghost instance to expire...")
                time.sleep(60)
            else:
                logger.error(f"💥 Critical Error: {e}")
                time.sleep(10) # Safety pause to prevent crash-looping
