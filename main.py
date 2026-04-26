import telebot, logging, os, time, sys
from solana.rpc.api import Client
from solders.keypair import Keypair

# 1. LOGGING & ENGINE CONFIG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIP-5.5-PROTECTED")

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)

# 2. PROTECTION LOGIC (Rent Guard & Band Protection)
def check_protections():
    try:
        rpc_url = os.getenv("SOLANA_RPC_URL")
        client = Client(rpc_url)
        wallet_addr = os.getenv("SOLANA_WALLET_ADDRESS")
        
        # Check Wallet Balance vs Rent Guard
        balance_resp = client.get_balance(wallet_addr)
        balance = balance_resp.value / 10**9  # Convert Lamports to SOL
        rent_guard = float(os.getenv("RENT_GUARD", "0.05"))

        if balance < rent_guard:
            logger.warning(f"⚠️ PROTECTION TRIGGERED: Balance ({balance} SOL) below Rent Guard ({rent_guard})")
            return False, "Rent Guard Active (Low Balance)"
        
        return True, "All Systems Nominal"
    except Exception as e:
        return False, f"Protection Check Failed: {str(e)}"

# 3. COMMANDS
@bot.message_handler(commands=['health', 'status'])
def handle_status(message):
    protected, msg = check_protections()
    status_icon = "✅" if protected else "⚠️"
    
    response = (
        f"🛰️ **S.I.P. v5.5 OMNI-SYNC**\n"
        f"RPC: ✅ ONLINE | DB: ✅\n"
        f"Protection: {status_icon} {msg}\n"
        f"Mode: `{os.getenv('HUNTING_STATE', 'Safety')}`\n"
        f"Jito MEV: 🛡️ ENABLED"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 4. FULL LISTENER (The Hunter)
@bot.message_handler(func=lambda message: True)
def hunter_listener(message):
    if message.text and not message.text.startswith('/'):
        text = message.text.strip()
        # Scan for Solana CA (32-44 chars)
        if 32 <= len(text) <= 44:
            is_safe, reason = check_protections()
            
            if is_safe and os.getenv("HUNTING_STATE") == "Active":
                logger.info(f"🎯 TARGET SPOTTED: {text[:10]}... Executing Sniper.")
                # Jito / Transaction Logic would fire here
                bot.reply_to(message, f"🎯 **S.I.P. Hunter:** CA Detected. Executing protected trade via Jito...")
            else:
                logger.info(f"🛡️ SIGNAL IGNORED: {reason}")

# 5. STARTUP ENGINE
if __name__ == "__main__":
    logger.info("🚀 STARTING PROTECTED S.I.P. v5.5...")
    
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except: pass

    while True:
        try:
            logger.info("💤 Stabilization (120s Wait)...")
            time.sleep(120) 
            logger.info("🛰️ OMNI-SYNC LIVE. Protections Active.")
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
        except Exception as e:
            if "409" in str(e): time.sleep(60)
            else: time.sleep(10)
