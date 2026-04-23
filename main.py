import os
import redis
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE CONNECTION ---
# This will attempt to connect to your live data. 
# If it can't find Redis, it defaults to a local connection (which will be empty/zeros).
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL, decode_responses=True)

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KRAKEN_WALLET = os.getenv("KRAKEN_WALLET", "junT...1twS")
PROTOCOL_FEE = 0.01

# --- FLASK HEARTBEAT ---
app = Flask(__name__)
@app.route('/')
def health(): return "Sovereign Protocol Online", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- REAL REVENUE LOGIC (NO FAKE DATA) ---
def get_live_stats():
    try:
        # We pull directly from keys. If the key doesn't exist, it returns 0.
        vol = float(r.get("total_volume_sol") or 0.0)
        leads = int(r.get("active_leads_count") or 0)
        fees = vol * PROTOCOL_FEE
        return vol, fees, leads
    except Exception as e:
        logging.error(f"Database connection issue: {e}")
        return 0.0, 0.0, 0
      
# --- BOT COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vol, fees, leads = get_live_stats()
    
    msg = (
        "⚡️ **SOVEREIGN PROTOCOL: LIVE DATA**\n\n"
        f"🛰 **Status:** Monitoring Redis Feed\n"
        f"🏦 **Destination:** Kraken\n"
        f"💳 **Wallet:** `{KRAKEN_WALLET}`\n"
        "\n--- **ACTUAL REVENUE** ---\n"
        f"💵 **Gross Fees:** {fees:.6f} SOL\n"
        f"📈 **Total Volume:** {vol:.2f} SOL\n"
        f"🎯 **Active Leads:** {leads}\n"
        "\n--- --- --- --- ---\n"
        "🟢 *Displaying real-time database values only.*"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        app_bot = ApplicationBuilder().token(TOKEN).build()
        app_bot.add_handler(CommandHandler('start', start))
        app_bot.run_polling()
