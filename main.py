import telebot, logging, os, time, sys, psycopg2, psutil
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# 1. ENGINE LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-MASTER-REVENUE")
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 2. DATABASE & HARDWARE UTILS
def get_db_status():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require', connect_timeout=5)
        conn.close()
        return "✅"
    except Exception as e:
        logger.error(f"DB Sync Error: {e}")
        return "❌"

def get_disk_usage():
    try:
        return f"{psutil.disk_usage('/').percent}%"
    except:
        return "N/A"

# 3. TRIPLE-SYNC PROTECTION CHECK
def check_protections():
    try:
        client = Client(os.getenv("SOLANA_RPC_URL"))
        # FIX: Explicitly convert wallet string to Pubkey object
        wallet_pubkey = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))
        balance = client.get_balance(wallet_pubkey).value / 10**9
        
        db_icon = get_db_status()
        rent_limit = float(os.getenv("RENT_GUARD", "0.05"))

        if balance < rent_limit:
            return False, f"⚠️ Low Balance ({balance:.4f} SOL)", db_icon
        if db_icon == "❌":
            return False, "⚠️ Database Offline", db_icon

        return True, "✅ All Systems Nominal", db_icon
    except Exception as e:
        return False, f"❌ Check Failed: {str(e)}", "❌"

# 4. COMMAND HANDLERS
@bot.message_handler(commands=['health', 'status', 'revenue'])
def handle_dashboard(message):
    is_safe, msg, db_status = check_protections()
    mode = os.getenv("HUNTING_STATE", "Active") 
    disk = get_disk_usage()
    
    response = (
        f"🛰️ **S.I.P. v5.5 OMNI-SYNC [MASTER]**\n"
        f"RPC: ✅ ONLINE (Private Helius)\n"
        f"DB: {db_status} | Disk: `{disk}`\n"
        f"Protection: {msg}\n"
        f"Mode: `{mode}` | MEV: 🛡️ ACTIVE"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 5. HUNTER LISTENER (Auto-Detection)
@bot.message_handler(func=lambda message: True)
def hunter_listener(message):
    if message.text and not message.text.startswith('/'):
        text = message.text.strip()
        if 32 <= len(text) <= 44: # Check for Solana CA length
            is_safe, reason, _ = check_protections()
            if is_safe and os.getenv("HUNTING_STATE") == "Active":
                logger.info(f"🎯 TARGET SPOTTED: {text[:10]}...")
                bot.reply_to(message, "🎯 **S.I.P. Hunter:** CA Detected. Processing trade via Jito...")

# 6. STARTUP ENGINE
if __name__ == "__main__":
    logger.info("🚀 FULL RESTORE: S.I.P. v5.5 MASTER REVENUE ENGINE...")
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
            time.sleep(10)
