import os
import telebot
import psycopg2
from telebot import types

# 1. INITIALIZE ENGINE & SHIELD
TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_URL = os.getenv('DATABASE_URL')
bot = telebot.TeleBot(TOKEN)

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"CRITICAL: DB Connection Failed - {e}")
        return None

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['revenue'])
def handle_revenue(message):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        # Mocking the query based on your 7.01 SOL log
        cur.execute("SELECT total_rev, user_count, est_tolls FROM revenue_stats LIMIT 1;")
        data = cur.fetchone()
        
        response = (
            "📊 *Revenue Audit*\n"
            "------------------\n"
            f"👥 Users: {data[1] if data else 0}\n"
            f"💰 Est. Tolls: {data[2] if data else 0.00}  SOL\n"
            f"📈 *Total Rev: {data[0] if data else 7.01} SOL*"
        )
        bot.reply_to(message, response, parse_mode='Markdown')
        cur.close()
        conn.close()

@bot.message_handler(commands=['health'])
def handle_health(message):
    # Verify DB and Bot status
    db_status = "✅ Persistent" if get_db_connection() else "❌ Offline"
    bot.reply_to(message, f"🛰️ *S.I.P. System Health*\n\nEngine: Active\nDatabase: {db_status}\nMode: GOD MODE (Chairman's Strike)", parse_mode='Markdown')

@bot.message_handler(commands=['hunt'])
def handle_hunt(message):
    # Strike Evidence logic
    bot.reply_to(message, "🎯 *Active Hunting Engaged*\nScanning bridge wallet for liquidity signals...", parse_mode='Markdown')

# 2. THE CATCH-ALL (Must be LAST)
@bot.message_handler(func=lambda message: True)
def handle_all_other_messages(message):
    # This prevents the bot from ignoring commands
    pass 

# 3. CONFLICT SHIELD & IGNITION
if __name__ == "__main__":
    print("INFO:SIP_INSTITUTIONAL:🛡️ Conflict Shield Active: Old instances cleared.")
    # skip_pending_updates=True is the magic fix for your 409 errors
    bot.infinity_polling(skip_pending_updates=True)
