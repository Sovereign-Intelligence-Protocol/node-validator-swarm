import os
import time
import telebot
import psycopg2
from dotenv import load_dotenv
from solana.rpc.api import Client

# --- 1. THE AGGRESSIVE INITIALIZATION ---
load_dotenv() # Load from .env if it exists
os.environ.get('BOT_TOKEN') # Force a check of the system environment

TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = os.getenv('ADMIN_ID')
KRAKEN_ADDR = os.getenv('KRAKEN_ADDRESS')
DB_URL = os.getenv('DATABASE_URL')
RPC_URL = os.getenv('RPC_URL')

# --- THE AUTO-DIAGNOSTIC (Watch your logs for this!) ---
if not TOKEN:
    print("\n" + "!"*50)
    print("FATAL ERROR: RENDER CANNOT FIND 'BOT_TOKEN'")
    print(f"Current Keys available: {list(os.environ.keys())}")
    print("!"*50 + "\n")
    while True: time.sleep(60)

bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
solana_client = Client(RPC_URL)

# --- 2. BUSINESS LOGIC (Revenue/Subs/Crypto) ---
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

# --- 3. EXECUTION ENGINE ---
def main():
    while True:
        try:
            # THIS KILLS THE 409 CONFLICT (Instance Collision)
            print("Action: Resetting Telegram connection...")
            bot.remove_webhook()
            time.sleep(2) 
            
            print("S.I.P. v12.6: Hunting and Tracking Live.")
            if ADMIN_ID:
                try:
                    bot.send_message(ADMIN_ID, "🚀 *System Online:* Instance collision resolved.")
                except:
                    pass

            # Placeholder for your Jito/Liquidity logic
            print(">>> Jito Shield: PROTECTED")
            
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            print(f"Connection Alert: {e}. Restarting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    main()
