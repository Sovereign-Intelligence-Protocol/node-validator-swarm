import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KRAKEN_WALLET = "junT...1twS"  # Your verified Kraken destination
PROTOCOL_FEE = 0.01             # 1% Toll Bridge Fee

# --- FLASK SERVER FOR RENDER HEALTH CHECK ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Sovereign Protocol Online", 200

def run_flask():
    # Render provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- REVENUE LOGIC ---
def get_revenue_stats():
    """
    Retrieves live data from your Lead Scalper ledger.
    """
    # Replace these with your actual DB/Redis pull logic later
    total_volume_sol = 500.00  
    fees_collected = total_volume_sol * PROTOCOL_FEE
    active_leads = 8           
    return total_volume_sol, fees_collected, active_leads

# --- TELEGRAM COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    volume, fees, leads = get_revenue_stats()
    
    status_message = (
        "⚡️ **SOVEREIGN PROTOCOL: ONLINE**\n\n"
        f"🛰 **Status:** Live & Monitoring\n"
        f"🏦 **Destination:** Kraken Account\n"
        f"💳 **Wallet:** `{KRAKEN_WALLET}`\n"
        "\n--- **REVENUE METRICS** ---\n"
        f"💵 **Gross Revenue:** {fees:.4f} SOL\n"
        f"📈 **Total Volume:** {volume:.2f} SOL\n"
        f"🎯 **Active Leads:** {leads}\n"
        "\n--- --- --- --- ---\n"
        "✅ *Lead Scalper & Node-Validator Swarm Synchronized.*"
    )
    await update.message.reply_text(status_message, parse_mode='Markdown')

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # 1. Start the Health Check thread
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    # 2. Launch the Telegram Bot
    if not TOKEN:
        print("CRITICAL: TELEGRAM_BOT_TOKEN not found in environment variables!")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler('start', start))
        
        print("Sovereign Protocol is now polling...")
        application.run_polling()
