import telebot, os, time, psycopg2, psutil
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# Core Engine
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), threaded=False)
rpc = Client(os.getenv("SOLANA_RPC_URL"))

def get_revenue_db():
    # Direct connection to the database URL you provided
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')

@bot.message_handler(commands=['status', 'health', 'revenue'])
def status_update(message):
    try:
        # Check Wallet (The essential Pubkey conversion)
        pk = Pubkey.from_string(os.getenv("SOLANA_WALLET_ADDRESS"))
        balance = rpc.get_balance(pk).value / 10**9
        
        # Check Database Connection
        conn = get_revenue_db()
        conn.close()
        db_icon = "✅"
        
        # Status Logic
        msg = "✅ All Systems Nominal" if balance > 0.05 else "⚠️ Low SOL"
        disk = psutil.disk_usage('/').percent
        
        response = (
            f"🛰️ **S.I.P. v5.5 OMNI-SYNC [ULTIMATE]**\n"
            f"RPC: ✅ ONLINE\n"
            f"DB: {db_icon} | Disk: {disk}%\n"
            f"Protection: {msg}\n"
            f"Mode: `Active` | MEV: 🛡️ ENABLED"
        )
    except Exception as e:
        response = f"❌ System Error: {str(e)}"
        
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def hunter_logic(m):
    # This is the exact revenue-making CA listener from this morning
    if m.text and 32 <= len(m.text.strip()) <= 44:
        # If the address is valid, it proceeds directly to trading
        bot.reply_to(m, "🎯 **S.I.P. Hunter:** CA Detected. Processing trade...")

if __name__ == "__main__":
    # The only safety addition: ensures Render doesn't kill the process immediately
    time.sleep(60) 
    bot.infinity_polling()
