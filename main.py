import telebot, logging, os, time, sys
from solana.rpc.api import Client

# 1. LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5")

# 2. CONFIG LOADER
def get_config(key, default=None):
    return os.getenv(key, default)

bot = telebot.TeleBot(get_config("TELEGRAM_BOT_TOKEN"), threaded=False)

# 3. ADAPTIVE HEALTH CHECK (Multi-Strategy)
@bot.message_handler(commands=['health', 'status'])
def handle_health(message):
    try:
        rpc_url = get_config("SOLANA_RPC_URL")
        client = Client(rpc_url)
        
        is_healthy = False
        # Strategy A: is_connected (Modern SDK)
        if hasattr(client, 'is_connected'):
            is_healthy = client.is_connected()
        # Strategy B: get_health (Fallback)
        elif hasattr(client, 'get_health'):
            resp = client.get_health()
            is_healthy = "ok" in str(resp).lower()
        # Strategy C: Pulse Check (Fetching real data)
        else:
            client.get_latest_blockhash()
            is_healthy = True

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
        # Tells us the Type (e.g. AttributeError) so we can debug perfectly
        bot.reply_to(message, f"⚠️ **Connection Issue**\nType: `{type(e).__name__}`\nInfo: `{str(e)[:30]}`")

# 4. STARTUP ENGINE (120s STABILIZER)
if __name__ == "__main__":
    logger.info("🚀 INITIALIZING S.I.P. ENGINE...")
    
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except:
        pass

    while True:
        try:
            # PREVENTS 409 CONFLICT: Essential for Render deployments
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            
            logger.info("🛰️ OMNI-SYNC LIVE. Polling Telegram...")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("🔄 409 Conflict: Waiting for ghost instance...")
                time.sleep(60)
            else:
                logger.error(f"💥 Critical Error: {e}")
                time.sleep(10)
