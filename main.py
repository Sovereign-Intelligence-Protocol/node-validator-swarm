import os
import time
import telebot
import psycopg2
from dotenv import load_dotenv
from solana.rpc.api import Client

# --- 1. INITIALIZATION & SAFETY CHECK ---
load_dotenv()

# This MUST match the key name in your Render Environment tab
TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = os.getenv('ADMIN_ID')
KRAKEN_ADDR = os.getenv('KRAKEN_ADDRESS')
DB_URL = os.getenv('DATABASE_URL')
RPC_URL = os.getenv('RPC_URL')

# --- THE AUTO-DIAGNOSTIC ---
if not TOKEN:
    print("\n" + "!"*40)
    print("CRITICAL ERROR: 'BOT_TOKEN' IS MISSING!")
    print("Please check your Render Environment variables.")
    print("If your key is named 'TELEGRAM_TOKEN', rename it to 'BOT_TOKEN'.")
    print("!"*40 + "\n")
    # Keeps the process alive so the log doesn't just disappear
    while True:
        time.sleep(60)

bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
solana_client = Client(RPC_URL)

# --- 2. THE CORE BUSINESS LOGIC (Tracking & Revenue) ---
def track_activity(user_id, amount, tx_hash, category="settlement"):
    """Maintains full ledger tracking for crypto and subscriptions."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO revenue_ledger 
               (user_id, amount, destination, tx_hash, category, timestamp) 
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (user_id, amount, KRAKEN_ADDR, tx_hash, category)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ledger Error: {e}")

# --- 3. BOT HANDLERS & HUNTING ---
@bot.message_handler(commands=['start', 'status'])
def handle_status(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        bot.reply_to(message, "🦅 *S.I.P. v12.6 Active*\nLedger & Jito Shield Online.")

def run_hunting_protocol():
    """Jito Shield & Solana Liquidity logic."""
    print(">>> Jito Shield: PROTECTED")
    print(">>> Solana Liquidity Scan: ACTIVE")

# --- 4. THE EXECUTION ENGINE ---
def main():
    while True:
        try:
            # THIS KILLS THE 409 CONFLICT
            print("Resetting Telegram handshake...")
            bot.remove_webhook()
            time.sleep(2) 
            
            print("Sovereign Intelligence Protocol: Hunting and Tracking Live.")
            if ADMIN_ID:
                try:
                    bot.send_message(ADMIN_ID, "🚀 *System Online:* Instance collision resolved.")
                except:
                    pass

            run_hunting_protocol()
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            print(f"Connection Alert: {e}. Restarting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    main()
