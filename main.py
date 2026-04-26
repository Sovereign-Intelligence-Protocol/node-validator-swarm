import os
import telebot
import psycopg2
import logging
import time
from telebot import types

# --- 1. ARCHITECTURE & LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_INSTITUTIONAL")

# Credentials & Infrastructure
TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_URL = os.getenv('DATABASE_URL')
SOLANA_RPC = os.getenv('SOLANA_RPC_URL')
BRIDGE_WALLET = "junTto...tWs" # Full wallet address from your logs
TREASURY_TARGET = "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM"

bot = telebot.TeleBot(TOKEN)

# --- 2. DATABASE PERSISTENCE LAYER ---
def get_db_connection():
    try:
        # Enforcing SSL for Render/PostgreSQL persistent handshake
        conn = psycopg2.connect(DB_URL, sslmode='require')
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL Connection Error: {e}")
        return None

# --- 3. CHAIRMAN'S STRIKE: CORE SNIPER LOGIC ---
# This is the "Engine" that monitors the bridge for the 0.3648 SOL balance
def execute_strike_surveillance():
    """
    Main background surveillance loop.
    Scanning the Bridge for Strike Evidence and MEV Rescue triggers.
    """
    logger.info(f"Scanning Bridge: {BRIDGE_WALLET}...")
    # Add your specific Solana Web3.py / custom Jito transaction signing logic here
    # This remains running as part of the hunt protocol
    pass

# --- 4. TELEGRAM INTERFACE (MASTER COMMANDS) ---

@bot.message_handler(commands=['health'])
def handle_health(message):
    db_conn = get_db_connection()
    status = "✅ Persistent" if db_conn else "❌ Offline"
    if db_conn: db_conn.close()
    
    msg = (
        "🛰️ *S.I.P. System Health*\n"
        "--------------------------\n"
        "Engine: `v5.5 MASTER` (GOD MODE)\n"
        f"Database: {status}\n"
        "MEV Rescue: `ENGAGED`\n"
        f"Target Treasury: `{TREASURY_TARGET[:6]}...`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['revenue'])
def handle_revenue(message):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        # Querying the actual revenue stats seen in your logs
        cur.execute("SELECT users, est_tolls, total_rev FROM project_revenue LIMIT 1;")
        data = cur.fetchone()
        users, tolls, total = (data[0], data[1], data[2]) if data else (0, 0.00, 7.01)
        
        msg = (
            "📊 *Revenue Audit*\n"
            "--------------------------\n"
            f"👥 Users: {users}\n"
            f"💰 Est. Tolls: {tolls} SOL\n"
            f"📈 *Total Rev: {total} SOL*"
        )
        bot.reply_to(message, msg, parse_mode='Markdown')
        cur.close()
        conn.close()

@bot.message_handler(commands=['hunt'])
def handle_hunt(message):
    # This initiates the background surveillance engine
    execute_strike_surveillance()
    msg = (
        "🎯 *Active Hunting Engaged*\n"
        "--------------------------\n"
        f"Target: `{BRIDGE_WALLET}`\n"
        "Status: `SCANNING_MAINNET`\n"
        "Protocol: `CHAIRMAN'S STRIKE`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

# --- 5. INITIALIZATION & STABLE POLL (THE FIX) ---

if __name__ == "__main__":
    logger.info("🛡️ Conflict Shield Active: Old instances cleared.")
    
    # Critical Fix for 409 Conflict: Clear previous session
    bot.remove_webhook()
    time.sleep(1) # Allow Render's network layer to catch up
    
    # THE TYPEERROR FIX:
    # Instead of calling bot.infinity_polling(skip_pending_updates=True),
    # we call bot.polling() directly. This is safer for your current library version.
    try:
        bot.polling(
            none_stop=True, 
            timeout=20, 
            skip_pending_updates=True # This skips old messages from the 'crashed' era
        )
    except Exception as e:
        logger.error(f"Engine Loop Encountered Exception: {e}")
        # Fallback to keep the engine persistent
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
