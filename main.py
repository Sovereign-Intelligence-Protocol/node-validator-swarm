import os
import asyncio
import logging
import telebot
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Final")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

class SIP_Controller:
    def __init__(self):
        try:
            bot.remove_webhook()
            self.seed_kp = Keypair.from_base58_string(SEED_PK)
            logger.info(f"✅ S.I.P. Engine Loaded | Wallet: {self.seed_kp.pubkey()}")
        except Exception as e:
            logger.error(f"❌ Startup Error: {e}")
            raise

    async def get_balance(self):
        try:
            resp = await solana_client.get_balance(self.seed_kp.pubkey())
            return resp.value / 1_000_000_000
        except: return 0.0

    async def send_status(self):
        bal = await self.get_balance()
        msg = (
            f"<b>🚀 S.I.P. ONLINE</b>\n\n"
            f"💰 <b>Wallet:</b> <code>{bal:.4f} SOL</code>\n"
            f"🛡️ <b>Status:</b> Active Hunting"
        )
        try: bot.send_message(ADMIN, msg)
        except Exception as e: logger.error(f"Telegram Fail: {e}")

# --- COMMANDS (Thread-Safe Fix) ---
@bot.message_handler(commands=['start', 'status'])
def handle_commands(message):
    if str(message.from_user.id) != ADMIN: return
    # Create a brand new event loop for this specific command thread
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sip = SIP_Controller()
        loop.run_until_complete(sip.send_status())
        loop.close()
    except Exception as e:
        logger.error(f"Command Error: {e}")

# --- MAIN ENGINE ---
async def main():
    sip = SIP_Controller()
    await sip.send_status()

    # Start the command listener in the background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, bot.infinity_polling)

    cycle = 0
    while True:
        try:
            if cycle % 60 == 0:
                logger.info(f"SIP Heartbeat | Cycle {cycle}")
            cycle += 1
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Main Loop Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
