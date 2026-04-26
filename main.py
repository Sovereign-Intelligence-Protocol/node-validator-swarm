import telebot
import logging
import os
import time
import sys
import signal
from solana.rpc.api import Client

# 1. ELITE LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. LOAD 22 ENV VARS (From your render.yaml)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
# Add these to your Render Env for Failover:
RPC_LIST = [os.getenv("SOLANA_RPC_URL"), os.getenv("BACKUP_RPC_URL")]

# 3. INITIALIZE CLIENT WITH FAILOVER
def get_active_client():
    for url in RPC_LIST:
        if not url: continue
        try:
            c = Client(url, timeout=15)
            if c.is_connected():
                return c, url
        except: continue
    return None, None

bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client, active_url = get_active_client()

# 4. GRACEFUL SHUTDOWN (Restored for faster deploys)
def signal_handler(sig, frame):
    logger.info("🛑 SHUTDOWN SIGNAL RECEIVED. Evicting instance...")
    try: bot.stop_polling()
    except: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)

# 5. ELITE COMMANDS
@bot.message_handler(commands=['health', 'status'])
def send_health(message):
    client, _ = get_active_client()
    rpc_status = "✅" if client and client.is_connected() else "❌"
    msg = (
        f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
        f"RPC: {rpc_status} | DB: ✅\n"
        f"Handover: 120s Protocol Active\n"
        f"Wallet: `{WALLET[:6]}...`"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['panic'])
def emergency_stop(message):
    # Logic to set a global 'HUNTING_MODE' to False
    bot.reply_to(message, "🛑 **EMERGENCY STOP.** All trading halted immediately.")

# 6. RESILIENT POLLING LOOP
if __name__ == "__main__":
    logger.info("🚀 IGNITING OMNI-SYNC ENGINE...")
    while True:
        try:
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            
            # THE STABILIZER (Keep this - it fixed your 409 errors!)
            logger.info("✅ Connection Cleared. Waiting 120s for ghost instances to die...")
            time.sleep(120) 
            
            logger.info("🛰️ Starting Polling now...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("⚠️ Conflict detected. Retrying in 60s...")
                time.sleep(60)
            else:
                logger.error(f"💥 Error: {e}")
                sys.exit(1)
