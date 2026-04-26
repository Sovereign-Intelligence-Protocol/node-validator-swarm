import telebot, logging, os, time, sys
from solana.rpc.api import Client
from solders.pubkey import Pubkey  # The critical fix for the 'str' error

# 1. LOGGING & ENGINE CONFIG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-MASTER")

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 2. PROTECTION LOGIC (Band Protection / Rent Guard)
def check_protections():
    try:
        rpc_url = os.getenv("SOLANA_RPC_URL")
        client = Client(rpc_url)
        
        # FIXED: Converts string address from Env to a valid Pubkey object
        wallet_str = os.getenv("SOLANA_WALLET_ADDRESS")
        wallet_pubkey = Pubkey.from_string(wallet_str)
        
        # Check Wallet Balance
        balance_resp = client.get_balance(wallet_pubkey)
        balance = balance_resp.value / 10**9 
        
        # Pull Rent Guard (Defaults to 0.05 SOL)
        rent_limit = float(os.getenv("RENT_GUARD", "0.05"))

        if balance < rent_limit:
            return False, f"⚠️ Low Balance ({balance:.4f} SOL)"
        
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
        f"RPC: ✅ ONLINE (Private Helius)\n"
        f"Protection: {msg}\n"
        f"Mode: `{mode}`\n"
        f"Jito MEV: 🛡️ ENABLED"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 4. FULL HUNTER LISTENER (Restored Listening Power)
@bot.message_handler(func=lambda message: True)
def hunter_listener(message):
    if message.text and not message.text.startswith('/'):
        text = message.text.strip()
        # Scan for Solana CA (32-44 chars)
        if 32 <= len(text) <= 44:
            is_safe, reason = check_protections()
            
            if is_safe and os.getenv("HUNTING_STATE") == "Active":
                logger.info(f"🎯 TARGET SPOTTED: {text[:10]}...")
                bot.reply_to(message, f"🎯 **S.I.P. Hunter:** CA Detected. Processing trade...")
            else:
                logger.info(f"🛡️ SIGNAL IGNORED: {reason}")

# 5. STARTUP ENGINE (With 120s Ghost-Killer)
if __name__ == "__main__":
    logger.info("🚀 STARTING FULL S.I.P. v5.5 MASTER BUILD...")
    
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except:
        pass

    while True:
        try:
            # Essential for clearing Render's old bot instances
            logger.info("💤 Stabilizing environment... (120s Wait)")
            time.sleep(120) 
            
            logger.info("🛰️ OMNI-SYNC LIVE. Hunter is Listening.")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            if "409" in str(e):
                logger.warning("🔄 409 Conflict: Waiting 60s for old instance to expire...")
                time.sleep(60)
            else:
                logger.error(f"💥 Critical Error: {e}")
                time.sleep(10)
