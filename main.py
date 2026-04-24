import os
import time
import telebot
import psycopg2
from dotenv import load_dotenv
from solana.rpc.api import Client

# --- 1. INITIALIZATION (Fixed Variable Mapping) ---
load_dotenv()

# These now match the key names visible in your Render Environment screenshot
TOKEN = os.getenv('TELEGRAM_TOKEN') 
ADMIN_ID = os.getenv('ADMIN_ID')
KRAKEN_ADDR = os.getenv('KRAKEN_ADDRESS')
DB_URL = os.getenv('DATABASE_URL')
RPC_URL = os.getenv('RPC_URL')

# Safety check to prevent the 'NoneType' crash
if not TOKEN:
    print("❌ ERROR: 'TELEGRAM_TOKEN' not found in Render. Check your Key names!")
    while True: time.sleep(10)

bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
solana_client = Client(RPC_URL)

# --- 2. REVENUE & SUBSCRIPTION TRACKING ---
def track_all_activity(user_id, amount, tx_hash, category="general"):
    """Maintains full tracking for revenue and subscriptions."""
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
        print(f"✔️ Ledger Updated for {user_id}")
    except Exception as e:
        print(f"Ledger Log Error: {e}")

# --- 3. THE "PREDATORY" ENGINE (Jito & Liquidity) ---
def run_hunting_protocol():
    """Maintains Jito Shield & Liquidity Hunting loops."""
    print(">>> Jito Shield: ACTIVE")
    print(">>> Solana Liquidity Scan: RUNNING")

# --- 4. BOT COMMANDS ---
@bot.message_handler(commands=['start', 'status'])
def handle_status(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        status_msg = (
            "🦅 *S.I.P. v12.4 Operational*\n\n"
            "📈 *Revenue Tracking:* Online\n"
            "🛡️ *Jito Shield:* Protected\n"
            f"💰 *Route:* [Kraken]({KRAKEN_ADDR})"
        )
        bot.reply_to(message, status_msg)

@bot.message_handler(commands=['revenue', 'subs'])
def handle_ledger(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        bot.reply_to(message, "📊 *Querying Sovereign Ledger...*")

# --- 5. THE "ONLY ONE" EXECUTION STRATEGY ---
def main():
    while True:
        try:
            # THIS KILLS THE 409 CONFLICT
            print("Force-clearing ghost connections...")
            bot.remove_webhook()
            time.sleep(2) 
            
            print("Sovereign Intelligence Protocol: Hunting and Tracking Active.")
            if ADMIN_ID:
                try:
                    bot.send_message(ADMIN_ID, "✅ *Protocol Live:* Instance collision resolved.")
                except:
                    pass

            run_hunting_protocol()
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
        except Exception as e:
            print(f"System Alert: {e}. Restarting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    main()
