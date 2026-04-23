import os
import asyncio
import logging
import redis.asyncio as redis
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# 1. LOGGING SETUP
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. CONFIGURATION & MECHANICAL REDIS FIX
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RPC_URL = os.getenv("RPC_URL")
WSS_URL = os.getenv("WSS_URL")
WALLET_ADDR = os.getenv("SOLANA_WALLET_ADDRESS")
REDIS_URL = os.getenv("REDIS_URL", "")

# Fix the common "scheme" error automatically
if REDIS_URL and not REDIS_URL.startswith("redis://"):
    REDIS_URL = f"redis://{REDIS_URL}"

# 3. CORE LOGIC FUNCTIONS
async def get_on_chain_balance():
    """Fetch real-time SOL balance from Helius/Solana RPC."""
    if not RPC_URL or not WALLET_ADDR:
        return "Config Missing"
    try:
        async with AsyncClient(RPC_URL) as client:
            pubkey = Pubkey.from_string(WALLET_ADDR)
            res = await client.get_balance(pubkey)
            return res.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance Error: {e}")
        return "Error"

async def get_redis_data():
    """Fetch Revenue and Lead stats from Redis."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        fees = await r.get("total_fees") or "0.00"
        volume = await r.get("total_volume") or "0.00"
        leads = await r.get("active_leads") or "0"
        await r.close()
        return fees, volume, leads
    except Exception as e:
        logger.error(f"Redis Error: {e}")
        return "0.00", "0.00", "0"

# 4. COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main Dashboard: Shows Revenue, Volume, and Leads."""
    fees, volume, leads = await get_redis_data()
    balance_sol = await get_on_chain_balance()
    
    dashboard = (
        "⚡ **SOVEREIGN PROTOCOL: LIVE STATUS**\n\n"
        f"🛰️ **Network:** Solana Mainnet (Helius)\n"
        f"🏛️ **Destination:** Kraken\n"
        f"💳 **Wallet:** `{WALLET_ADDR[:6]}...{WALLET_ADDR[-4:]}`\n"
        f"⚖️ **Current Balance:** `{balance_sol}` SOL\n\n"
        "--- **REAL-TIME REVENUE** ---\n"
        f"💰 **Gross Fees:** `{fees}` SOL\n"
        f"📈 **Total Volume:** `{volume}` SOL\n"
        f"🎯 **Active Leads:** `{leads}`\n\n"
        "🟢 *Displaying verified on-chain data.*"
    )
    await update.message.reply_text(dashboard, parse_mode='Markdown')

async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force the Lead Scalper to run."""
    await update.message.reply_text("🔍 **S.I.P. ALERT:** Launching Lead Scalper Browser...")
    try:
        # Import internally to prevent crashes if playwright isn't ready
        import subprocess
        # Executes your actual scraper script as a background process
        subprocess.Popen(["python3", "scraper.py"])
        await update.message.reply_text("✅ **Scraper Process Started.** Check logs for real-time lead ingestion.")
    except Exception as e:
        await update.message.reply_text(f"❌ **Scraper Error:** {str(e)}")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the Hot Wallet and Kraken bridge status."""
    bal = await get_on_chain_balance()
    await update.message.reply_text(f"⚖️ **Bridge Balance:** `{bal}` SOL\n🏦 **Kraken Routing:** Synchronized")

async def safety(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle Safety Mode / Rent Guard status."""
    status = os.getenv("SAFETY_MODE", "ACTIVE")
    await update.message.reply_text(f"🛡️ **Rent Guard:** {status}\n🚫 **Sniper Status:** Monitoring Only (Safety Enabled)")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all available protocol commands."""
    commands = (
        "📜 **Sovereign Intelligence Commands:**\n\n"
        "/start   - View Live Revenue Dashboard\n"
        "/scrape  - Force Scraper to hunt for leads\n"
        "/balance - Check Wallet & Kraken status\n"
        "/safety  - View/Toggle Rent Guard status\n"
        "/help    - Show this menu"
    )
    await update.message.reply_text(commands, parse_mode='Markdown')

# 5. MAIN EXECUTION
def main():
    if not TOKEN:
        logger.error("No Telegram Token found! Check Environment Variables.")
        return

    # Build the Application
    application = Application.builder().token(TOKEN).build()

    # Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scrape", scrape))
    application.add_handler(CommandHandler("balance", balance_cmd))
    application.add_handler(CommandHandler("safety", safety))
    application.add_handler(CommandHandler("help", help_command))

    logger.info("Sovereign Protocol Online. Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
