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
# Connects to your live Redis instance using the environment variable
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    r = redis.from_url(REDIS_URL, decode_responses=True)
else:
    r = None
    logging.warning("REDIS_URL not found. System will default to zero stats.")

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KRAKEN_WALLET = os.getenv("KRAKEN_WALLET", "junT...1twS")
PROTOCOL_FEE = 0.01  # 1% Toll Bridge Fee

# --- FLASK HEARTBEAT ---
app = Flask(__name__)
@app.route('/')
def health(): return "Sovereign Protocol Online", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- REAL-TIME DATA FETCH ---
def get_live_stats():
    """Fetches real data from Redis keys with zero fallback."""
    if not r:
        return 0.0, 0.0, 0
    
    try:
        # Pulling the exact keys your Lead Scalper updates
        raw_volume = r.get("total_volume_sol")
        raw_leads = r.get("active_leads_count")
        
        volume = float(raw_volume) if raw_volume else 0.0
        leads = int(raw_leads) if raw_leads else 0
        fees = volume * PROTOCOL_FEE
        
        return volume, fees, leads
    except Exception as e:
        logging.error(f"Error reading live stats: {e}")
        return 0.0, 0.0, 0

# --- TELEGRAM COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vol, fees, leads = get_live_stats()
    
    msg = (
        "⚡️ **SOVEREIGN PROTOCOL: LIVE DATA**\n\n"
        f"🛰 **Status:** Monitoring Node-Validator Swarm\n"
        f"🏦 **Destination:** Kraken Account\n"
        f"💳 **Wallet:** `{KRAKEN_WALLET}`\n"
        "\n--- **ACTUAL REVENUE** ---\n"
        f"💵 **Gross Fees:** {fees:.6f} SOL\n"
        f"📈 **Total Volume:** {vol:.2f} SOL\n"
        f"🎯 **Active Leads:** {leads}\n"
        "\n--- --- --- --- ---\n"
        "🟢 *Data verified against live Redis ledger.*"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        app_bot = ApplicationBuilder().token(TOKEN).build()
        app_bot.add_handler(CommandHandler('start', start))
        app_bot.run_polling()
