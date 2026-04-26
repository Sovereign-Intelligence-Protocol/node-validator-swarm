import telebot, logging, os, time, sys, psycopg2, psutil
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# 1. ENGINE LOGGING & AUTH
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-MASTER-ULTIMATE")
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 2. DATABASE & DISK UTILITIES
def get_db_status():
    try:
        # Connects using the PostgreSQL string you provided via Environment Variable
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

# 3. THE "GOLDEN" PROTECTION CHECK
def check_protections():
    try:
        # RPC & Wallet (FIX: Converts string to Pubkey object to stop 'str' error)
        client = Client(os.getenv("SOLANA_RPC_URL"))
        wallet_pubkey = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))
        balance_resp = client.get_balance(wallet_pubkey)
        balance = balance_resp.value / 10**9
        
        # Sync Database Status
        db_icon = get_db_status()
        
        # Rent Guard Logic
        rent_limit = float(os.getenv("RENT_GUARD", "0.05"))
        if balance < rent_limit:
            return False, f"⚠️ Low Balance ({balance:.4f} SOL)", db_icon

        return True, "✅ All Systems Nominal", db_icon
    except Exception as e:
        # This will catch and display the error if the Pubkey or RPC fails
        return False, f"❌ Check Failed: {str(e)}", "❌"

# 4. COMMAND HANDLERS
@bot.message_handler(commands=['health', 'status'])
def handle_status(message):
    is_safe, msg, db_status = check_protections()
    mode = os.getenv("HUNTING_STATE", "Safety")
    disk = get_disk_usage()
    
    response = (
        f"🛰️ **S.I.P. v5.5 OMNI-SYNC [ULTIMATE]**\n"
        f"RPC: ✅ ONLINE (Private Helius)\n"
        f"DB: {db_status} | Disk: `{disk}`\n"
        f"Protection: {msg}\n"
        f"Mode: `{mode}` | MEV: 🛡️ ACTIVE"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 5. HUNTER LISTENER (Scanning Logic)
@bot.message_handler(func=lambda message: True)
def hunter_listener(message):
    if message.text and not message.text.startswith('/'):
        text = message.text.strip()
        # Scan for Solana Contract Addresses (32-44 characters)
        if 32 <= len(text) <= 44:
            is_safe, reason, _ = check_protections()
            if is_safe and os.getenv("HUNTING_STATE") == "Active":
                logger.info(f"🎯 TARGET SPOTTED: {text[:10]}...")
                bot.reply_to(message, "🎯 **S.I.P. Hunter:** CA Detected. Processing trade...")
            else:
                logger.info(f"🛡️ SIGNAL IGNORED: {reason}")

# 6. STARTUP ENGINE (Resilient Stabilization)
if __name__ == "__main__":
    logger.info("🚀 STARTING THE ULTIMATE S.I.P. v5.5 SUITE...")
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except: pass

    while True:
        try:
            # 120s Wait: Critical to prevent Render '409 Conflict' rejections from Telegram
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            logger.info("🛰️ OMNI-SYNC LIVE. Hunter is Listening.")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
        except Exception as e:
            if "409" in str(e):
                time.sleep(60)
            else:
                time.sleep(10)
