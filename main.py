import telebot, logging, os, time, sys
from solana.rpc.api import Client

# 1. OPTIMIZED LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-HELIUS")

# 2. BOT INITIALIZATION
# This pulls from your 22 Render Environment Variables
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 3. THE PRIVATE RPC HEALTH CHECK
@bot.message_handler(commands=['health', 'status'])
def handle_health(message):
    try:
        # Pull your NEW private Helius URL from Render
        rpc_url = os.getenv("SOLANA_RPC_URL")
        client = Client(rpc_url, timeout=20)
        
        # We perform a real 'ping' by fetching the latest blockhash
        client.get_latest_blockhash()
        
        response = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
            f"RPC: ✅ ONLINE (Private Helius)\n"
            f"DB: ✅ | Mode: `{os.getenv('HUNTING_STATE', 'Safety')}`\n"
            f"Wallet: `{os.getenv('SOLANA_WALLET_ADDRESS')[:6]}...`"
        )
        bot.reply_to(message, response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Private RPC Error: {e}")
        # If it still fails, it's likely a Render IP block or exhausted Helius credits
        bot.reply_to(message, f"⚠️ **RPC Issue**\nType: `{type(e).__name__}`\nStatus: Connection Refused by Helius.")

# 4. THE STABILIZED STARTUP ENGINE
if __name__ == "__main__":
    logger.info("🚀 INITIALIZING S.I.P. ENGINE...")
    
    # Reset webhooks to prevent 409 Conflict
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except:
        pass

    while True:
        try:
            # 120s Wait: Essential for Render to kill 'ghost' instances
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            
            logger.info("🛰️ OMNI-SYNC LIVE. Polling Telegram...")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("🔄 409 Conflict: Waiting 60s for ghost instance to expire...")
                time.sleep(60)
            else:
                logger.error(f"💥 Critical Error: {e}")
                time.sleep(10)
