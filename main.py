import os
import asyncio
import logging
import telebot
import threading
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Final")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# --- CORE LOGIC ---
async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except:
        return 0.0

def send_sync_report():
    """Sync wrapper to send the report without loop conflicts."""
    try:
        # Create a temporary loop just for this one-off check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        kp = Keypair.from_base58_string(SEED_PK)
        bal = loop.run_until_complete(get_balance(kp.pubkey()))
        
        msg = (
            f"<b>🚀 S.I.P. ONLINE</b>\n\n"
            f"💰 <b>Wallet:</b> <code>{bal:.4f} SOL</code>\n"
            f"🛡️ <b>Status:</b> Active Hunting"
        )
        bot.send_message(ADMIN, msg)
        loop.close()
    except Exception as e:
        logger.error(f"Report Error: {e}")

# --- TELEGRAM COMMANDS ---
@bot.message_handler(commands=['start', 'status'])
def handle_commands(message):
    if str(message.from_user.id) == ADMIN:
        send_sync_report()

# --- MAIN RUNNER ---
def run_bot_polling():
    """Runs in a separate thread to listen for your messages."""
    bot.remove_webhook()
    logger.info("📡 Bot Listener Started...")
    bot.infinity_polling(non_stop=True, timeout=60)

async def main_engine():
    """Main loop for hunting and automated checks."""
    logger.info("🚀 S.I.P. Engine Starting...")
    
    # Start the Telegram Listener in the background
    threading.Thread(target=run_bot_polling, daemon=True).start()
    
    # Send initial status
    send_sync_report()

    cycle = 0
    while True:
        try:
            if cycle % 60 == 0:
                logger.info(f"Heartbeat | Cycle {cycle}")
            
            cycle += 1
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Engine Loop Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main_engine())
