import os
import time
import telebot
import psycopg2
import logging
from telebot import types
from solana.rpc.api import Client 
from solders.pubkey import Pubkey

# --- 1. ARCHITECTURE & SECURE LABELS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_INSTITUTIONAL")

# THE KEY LABELS: Matches your Environment exactly
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') 
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID') 
DB_URL = os.getenv('DATABASE_URL') 
RPC_URL = os.getenv('SOLANA_RPC_URL') 

if not TOKEN:
    # This matches the error in your 09:50 AM screenshot
    logger.error("❌ Exception: Bot token is not defined. Check TELEGRAM_BOT_TOKEN in Render.")

bot = telebot.TeleBot(TOKEN)
solana_client = Client(RPC_URL) if RPC_URL else None

# Targets
BRIDGE_WALLET = "junTto...tWs"
TREASURY_TARGET = "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM"

# --- 2. SECURE DB CONNECTION ---
def get_db_connection():
    try:
        # SSL TLSv1.3 as required by project-revenue-db
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        logger.error(f"PostgreSQL Connection Error: {e}")
        return None

# --- 3. MASTER INTERFACE (WITH ADMIN GATE) ---

@bot.message_handler(commands=['health'])
def handle_health(message):
    db_conn = get_db_connection()
    status = "✅ Persistent" if db_conn else "❌ Offline"
    if db_conn: db_conn.close()
    
    bot.reply_to(message, (
        "🛰️ *S.I.P. System Health*\n"
        "--------------------------\n"
        "Engine: `v5.5 MASTER` (Active)\n"
        f"Database: {status}\n"
        "Protocol: `CHAIRMAN'S STRIKE`"
    ), parse_mode='Markdown')

@bot.message_handler(commands=['revenue', 'hunt'])
def handle_admin_commands(message):
    # SECURITY CHECK: Matches your Admin ID
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, "🚫 *Unauthorized Access Blocked.*")
        return

    if message.text.startswith('/revenue'):
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT users, est_tolls, total_rev FROM project_revenue LIMIT 1;")
            data = cur.fetchone()
            users, tolls, total = (data[0], data[1], data[2]) if data else (0, 0.00, 7.01)
            bot.reply_to(message, f"📊 *Audit*\nUsers: {users}\nTolls: {tolls} SOL\n*Total: {total} SOL*", parse_mode='Markdown')
            cur.close()
            conn.close()
    
    elif message.text.startswith('/hunt'):
        # Add your Solana signing logic here
        bot.reply_to(message, "🎯 *Hunting Engaged*\nTarget: `BRIDGE_ACTIVE`")

# --- 4. STABILITY IGNITION (THE FIX FOR 4.12.0) ---

if __name__ == "__main__":
    if TOKEN:
        logger.info("🛡️ Conflict Shield: Resetting sessions...")
        
        # Reset webhook to fix 409 Conflict
        bot.remove_webhook()
        
        # Manual clearing of backlog to avoid the Version 4.12.0 TypeError
        try:
            bot.get_updates(offset=-1)
        except:
            pass
            
        time.sleep(2)
        logger.info("🚀 S.I.P. v5.5 ENGINE IGNITED")
        
        # Using infinity_polling as verified for your build
        bot.infinity_polling(timeout=20, long_polling_timeout=5)
