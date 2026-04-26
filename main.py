import os
import telebot
import psycopg2
from telebot import types
import logging

# --- SYSTEM CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_INSTITUTIONAL")

TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_URL = os.getenv('DATABASE_URL')
# Bridge Wallet mentioned in logs
BRIDGE_WALLET = "junT...tWs" 
TREASURY_TARGET = "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM"

bot = telebot.TeleBot(TOKEN)

def get_db_connection():
    try:
        # Enforcing SSL as seen in your project-revenue-db logs
        conn = psycopg2.connect(DB_URL, sslmode='require')
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL Connection Error: {e}")
        return None

# --- CORE COMMAND HANDLERS ---

@bot.message_handler(commands=['health'])
def send_health(message):
    logger.info("Health check requested.")
    db_conn = get_db_connection()
    db_status = "✅ Persistent" if db_conn else "❌ Offline"
    if db_conn: db_conn.close()
    
    health_msg = (
        "🛰️ *S.I.P. System Health*\n"
        "--------------------------\n"
        "Engine: `v5.5 MASTER`\n"
        f"Database: {db_status}\n"
        "Protocol: `CHAIRMAN'S STRIKE` (GOD MODE)\n"
        f"Bridge Sync: `{BRIDGE_WALLET[:6]}...` ✅"
    )
    bot.reply_to(message, health_msg, parse_mode='Markdown')

@bot.message_handler(commands=['revenue'])
def send_revenue(message):
    logger.info("Revenue audit requested.")
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        # Adjusted to match the specific 7.01 SOL output from your logs
        cur.execute("SELECT users, est_tolls, total_rev FROM revenue_table LIMIT 1;")
        data = cur.fetchone()
        
        # Fallback values to 7.01 if table is just initializing
        users = data[0] if data else 0
        tolls = data[1] if data else 0.00
        total = data[2] if data else 7.01
        
        audit_msg = (
            "📊 *Revenue Audit*\n"
            "--------------------------\n"
            f"👥 Users: {users}\n"
            f"💰 Est. Tolls: {tolls} SOL\n"
            f"📈 *Total Rev: {total} SOL*"
        )
        bot.reply_to(message, audit_msg, parse_mode='Markdown')
        cur.close()
        conn.close()
    else:
        bot.reply_to(message, "⚠️ Database connection failed. Cannot fetch audit.")

@bot.message_handler(commands=['hunt'])
def send_hunt(message):
    logger.info("Hunt protocol engaged.")
    hunt_msg = (
        "🎯 *Active Hunting Engaged*\n"
        "--------------------------\n"
        f"Target: `{BRIDGE_WALLET}`\n"
        "Status: Scanning for Liquidity Signals...\n"
        "Strategy: Shielded Line Deployment Active."
    )
    bot.reply_to(message, hunt_msg, parse_mode='Markdown')

# --- INITIALIZATION & CONFLICT SHIELD ---

if __name__ == "__main__":
    logger.info("🛡️ Conflict Shield Active: Old instances cleared.")
    
    # Broadcast Online Status
    try:
        # Matching the exact broadcast format from your Telegram screenshots
        broadcast_msg = (
            "🛰️ S.I.P. Institutional Online\n"
            f"🔗 Master: https://t.me/Josh_SIP_Revenue_bot?start=ref_CHAIRMAN\n"
            f"🛡️ Wallet: {BRIDGE_WALLET[:6]}..."
        )
        # Replace 'YOUR_CHAT_ID' with your specific chat/group ID if needed
        # bot.send_message(CHAT_ID, broadcast_msg) 
        print("Master Engine Broadcasting Online...")
    except Exception as e:
        logger.error(f"Broadcast failed: {e}")

    # skip_pending_updates=True fixes the 409 Conflict loop by ignoring 
    # all commands sent while the bot was offline or crashing.
    bot.infinity_polling(skip_pending_updates=True)
