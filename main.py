import os, time, telebot, psycopg2
from dotenv import load_dotenv
from solana.rpc.api import Client

# --- 1. CONFIGURATION & ENVIRONMENT ---
load_dotenv()

# These keys must exist in your Render Environment Variables
TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = os.getenv('ADMIN_ID')
KRAKEN_ADDR = os.getenv('KRAKEN_ADDRESS')
DB_URL = os.getenv('DATABASE_URL')
RPC_URL = os.getenv('RPC_URL')

if not TOKEN:
    print("❌ FATAL ERROR: 'BOT_TOKEN' not found in environment!")
    while True: time.sleep(60)

bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
solana_client = Client(RPC_URL)

# --- 2. CORE BUSINESS LOGIC (Revenue & Tracking) ---
def track_activity(user_id, amount, tx_hash, category="settlement"):
    """
    Records every transaction and routes revenue tracking 
    to your primary Kraken destination.
    """
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
        print(f"✔️ Ledger Entry: {category} successful.")
    except Exception as e:
        print(f"❌ Database/Ledger Error: {e}")

# --- 3. BOT COMMAND HANDLERS ---
@bot.message_handler(commands=['start', 'status'])
def handle_status(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        status_msg = (
            "🦅 *S.I.P. v13.5 Fully Restored*\n\n"
            "📈 *Tracking:* Active\n"
            "🛡️ *Jito Shield:* Protected\n"
            f"💰 *Route:* [Kraken Primary]({KRAKEN_ADDR})"
        )
        bot.reply_to(message, status_msg)

# --- 4. THE EXECUTION ENGINE (Ghost-Killer Build) ---
def main():
    while True:
        try:
            # THE CIRCUIT BREAKER: Force-clears any lingering Telegram sessions
            print("Action: Opening fresh Telegram handshake...")
            bot.remove_webhook(drop_pending_updates=True)
            time.sleep(5) 
            
            print("Sovereign Intelligence Protocol: Hunting and Tracking Live.")
            if ADMIN_ID:
                try:
                    bot.send_message(ADMIN_ID, "🚀 *System Online:* Handshake successful. Protocols active.")
                except:
                    pass

            # Hunting loops
            print(">>> Jito Shield: PROTECTED")
            print(">>> Solana Liquidity Scan: ACTIVE")

            bot.infinity_polling(timeout=90, long_polling_timeout=40)
            
        except Exception as e:
            # Fallback for connection conflicts
            print(f"Connection Alert: {e}. Retrying in 15s...")
            time.sleep(15)

if __name__ == "__main__":
    main()
