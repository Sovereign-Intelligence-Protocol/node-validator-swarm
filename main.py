import os, time, telebot, psycopg2
from dotenv import load_dotenv

load_dotenv()
# THE FIX: Ensure this name matches your Render Environment Key exactly
TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = os.getenv('ADMIN_ID')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'status'])
def status(m):
    if str(m.from_user.id) == str(ADMIN_ID):
        bot.reply_to(m, "🦅 S.I.P. Online. Revenue & Jito Active.")

def main():
    while True:
        try:
            # THE CIRCUIT BREAKER: Kills the '409 Conflict' immediately
            print("Cleaning old sessions...")
            bot.remove_webhook(drop_pending_updates=True)
            time.sleep(5) 
            
            print("Sovereign Protocol: Hunting Live.")
            bot.infinity_polling(timeout=90)
        except Exception as e:
            print(f"Conflict: {e}. Retrying...")
            time.sleep(15)

if __name__ == "__main__":
    main()
