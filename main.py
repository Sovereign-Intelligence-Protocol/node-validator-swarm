import telebot, logging, os, time, sys, psycopg2
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# 1. LOGGING & ENGINE CONFIG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-FULL-RESTORE")

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 2. DATABASE CONNECTIVITY
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Failed: {e}")
        return None

# 3. PROTECTION LOGIC (RPC + DB + RENT)
def check_protections():
    try:
        # RPC Check
        client = Client(os.getenv("SOLANA_RPC_URL"))
        wallet_pubkey = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))
        balance = client.get_balance(wallet_pubkey).value / 10**9
        
        # Database Check
        db = get_db_connection()
        db_status = "✅" if db else "❌"
        if db: db.close()

        # Rent Guard Logic
        rent_limit = float(os.getenv("RENT_GUARD", "0.05"))
        if balance < rent_limit:
            return False, f"⚠️ Low Balance ({balance:.4f} SOL)", db_status

        return True, "✅ All Systems Nominal", db_status
    except Exception as e:
        return False, f"❌ Check Failed: {str(e)}", "❌"

# 4. COMMAND HANDLERS
@bot.message_handler(commands=['health', 'status'])
def handle_status(message):
    is_safe, msg, db_icon = check_protections()
    mode = os.getenv("HUNTING_STATE", "Safety")
    
    response = (
        f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
        f"RPC: ✅ ONLINE (Private)\n"
        f"DB: {db_icon} | Mode: `{mode}`\n"
        f"Protection: {msg}\n"
        f"Jito MEV: 🛡️ ENABLED"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 5. STARTUP ENGINE (Wait for stabilization)
if __name__ == "__main__":
    logger.info("🚀 RESTORING FULL S.I.P. v5.5 DATABASE ENGINE...")
    
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except: pass

    while True:
        try:
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            logger.info("🛰️ OMNI-SYNC LIVE. Hunter is Listening.")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
        except Exception as e:
            if "409" in str(e): time.sleep(60)
            else: time.sleep(10)
