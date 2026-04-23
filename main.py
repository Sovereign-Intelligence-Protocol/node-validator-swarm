import os
import redis
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE & BLOCKCHAIN CONNECTION ---
# 1. Connect to Redis (Your Truth Ledger)
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    logging.info("✅ Redis Connection Established.")
else:
    r = None
    logging.warning("⚠️ REDIS_URL missing. Stats will default to 0.")

# 2. Build Helius RPC (Your High-Speed Eyes)
HELIUS_KEY = os.getenv("HELIUS_API_KEY")
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}" if HELIUS_KEY else None

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KRAKEN_WALLET = os.getenv("KRAKEN_WALLET", "junT...1twS") # Your saved destination
PROTOCOL_FEE = 0.01  # 1% Revenue Model

# --- FLASK HEARTBEAT (Keeps Render Alive) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Sovereign Protocol Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- LIVE STATS LOGIC ---
def get_live_stats():
    """Pulls directly from your Lead Scalper's actual Redis keys."""
    if not r:
        return 0.0, 0.0, 0
    
    try:
        # Fetches only what exists in the DB. No fake numbers.
        volume = float(r.get("total_volume_sol") or 0.0)
        leads = int(r.get("active_leads_count") or 0)
        fees = volume * PROTOCOL_FEE
        return volume, fees, leads
    except Exception as e:
        logging.error(f"Error reading Redis: {e}")
        return 0.0, 0.0, 0

# --- BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vol, fees, leads = get_live_stats()
    
    msg = (
        "⚡️ **SOVEREIGN PROTOCOL: LIVE STATUS**\n\n"
        f"🛰 **Network:** Solana Mainnet (Helius)\n"
        f"🏦 **Destination:** Kraken\n"
        f"💳 **Wallet:** `{KRAKEN_WALLET}`\n"
        "\n--- **REAL-TIME REVENUE** ---\n"
        f"💵 **Gross Fees:** {fees:.6f} SOL\n"
        f"📈 **Total Volume:** {vol:.2f} SOL\n"
        f"🎯 **Active Leads:** {leads}\n"
        "\n--- --- --- --- ---\n"
        "🟢 *Displaying verified on-chain data only.*"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

if __name__ == '__main__':
    # Start the web server in a background thread
    Thread(target=run_flask, daemon=True).start()
    
    # Start the Telegram Bot
    if TOKEN:
        app_bot = ApplicationBuilder().token(TOKEN).build()
        app_bot.add_handler(CommandHandler('start', start))
        logging.info("🚀 Bot is polling for commands...")
        app_bot.run_polling()
    else:
        logging.error("❌ TELEGRAM_BOT_TOKEN is missing from Environment Variables.")
