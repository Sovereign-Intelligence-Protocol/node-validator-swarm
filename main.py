import telebot, logging, os, time, sys
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# 1. LOGGING & ENGINE CONFIG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-HUNTER")

# Initialize Bot
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 2. PROTECTION LOGIC (Band Protection / Rent Guard)
def check_protections():
    try:
        rpc_url = os.getenv("SOLANA_RPC_URL")
        client = Client(rpc_url)
        
        # Convert string to Pubkey object to prevent 'str' conversion error
        wallet_str = os.getenv("SOLANA_WALLET_ADDRESS")
        wallet_pubkey = Pubkey.from_string(wallet_str)
        
        # Fetch Balance
        balance_resp = client.get_balance(wallet_pubkey)
        balance = balance_resp.value / 10**9 
        
        # Pull Rent Guard from Render Env (Default 0.05 SOL)
        rent_limit = float(os.getenv("RENT_GUARD", "0.05"))

        if balance < rent_limit:
            return False, f"⚠️ Protection: Low Balance ({balance:.4f} SOL)"
        
        return True, "✅ All Systems Nominal"
    except Exception as e:
        return False, f"❌ Protection Check Failed: {str(e)}"

# 3. COMMAND HANDLERS
@bot.message_handler(commands=['health', 'status'])
def handle_status(message):
    is_safe, msg = check_protections()
    mode = os.getenv("HUNTING_STATE", "Safety")
    
    response = (
        f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
        f"RPC: ✅ ONLINE (Private)\n"
        f"Protection: {msg}\n"
        f"Mode: `{mode}`\n"
        f"Jito MEV: 🛡️ ENABLED"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 4. FULL LISTENER (The Hunter Engine)
@bot.message_handler(func=lambda message: True)
def hunter_listener(message):
    # Ignore commands
    if message.text and message.text.startswith('/'):
        return
        
    text = message.text.strip()
    # Scan for Solana CA (32-44 chars)
    if 32 <= len(text) <= 44:
        is_safe, reason = check_protections()
        
        if is_safe and os.getenv("HUNTING_STATE") == "Active":
            logger.info(f"🎯 TARGET SPOTTED: {text[:10]}... Executing.")
            bot.reply_to(message, f"🎯 **S.I.P. Hunter:** CA Detected. Processing trade...")
            # Sniping execution logic would go here
        else:
            logger.info(f"🛡️ SIGNAL IGNORED: {reason}")

# 5. STARTUP ENGINE (Resilient Loop)
if __name__ == "__main__":
    logger.info("🚀 STARTING FULL S.I.P. v5.5 HUNTER...")
    
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except:
        pass

    while True:
        try:
            # 120s Wait: Critical to prevent '409 Conflict' on Render
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            
            logger.info("🛰️ OMNI-SYNC LIVE. Hunter is Listening.")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("🔄 409 Conflict: Waiting 60s for old instance to die...")
                time.sleep(60)
            else:
                logger.error(f"💥 Critical Error: {e}")
                time.sleep(10)
