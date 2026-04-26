import telebot, logging, os, time, sys
from solana.rpc.api import Client

# 1. LOGGING (Optimized for Quiet Mode)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-QUIET")

# 2. CONFIG LOADER
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 3. LEAN HEALTH CHECK (Checks the "Pulse")
@bot.message_handler(commands=['health', 'status'])
def handle_health(message):
    try:
        # Strict 10s timeout to identify RPC blocks immediately
        client = Client(os.getenv("SOLANA_RPC_URL"), timeout=10)
        
        # We try to get the latest blockhash - if this fails, the RPC is truly down
        client.get_latest_blockhash()
        is_healthy = True

        response = (
            f"🛰️ **S.I.P. v5.5 [QUIET MODE]**\n"
            f"RPC: ✅ | Listening: 🔇 OFF\n"
            f"Wallet: `{os.getenv('SOLANA_WALLET_ADDRESS')[:6]}...`"
        )
        bot.reply_to(message, response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"RPC Connection Refused: {e}")
        bot.reply_to(message, f"⚠️ **RPC Issue**\nType: `{type(e).__name__}`\nStatus: Refused/Blocked")

# 4. STABILIZED STARTUP
if __name__ == "__main__":
    logger.info("🚀 INITIALIZING QUIET ENGINE...")
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except: pass

    while True:
        try:
            logger.info("💤 Stabilization (120s Wait)...")
            time.sleep(120) 
            logger.info("🛰️ LIVE. Awaiting Commands.")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
        except Exception as e:
            if "409" in str(e):
                time.sleep(60)
            else:
                time.sleep(10)
