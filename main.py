import os
import asyncio
import logging
import requests
import telebot
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
JITO_PK = os.getenv("JITO_SIGNER_PRIVATE_KEY") or os.getenv("JITO_KEY")
RUGCHECK_API_KEY = os.getenv("RUGCHECK_API_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Global Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Engine")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

class SIP_Controller:
    def __init__(self):
        try:
            bot.remove_webhook(drop_pending_updates=True)
            self.seed_kp = Keypair.from_base58_string(SEED_PK)
            self.jito_kp = Keypair.from_base58_string(JITO_PK) if JITO_PK else self.seed_kp
            self.threshold = 0.01
            logger.info(f"✅ S.I.P. Engine Ready | Wallet: {self.seed_kp.pubkey()}")
        except Exception as e:
            logger.error(f"❌ Initialization Error: {e}")
            raise

    async def get_balance(self, pubkey):
        try:
            resp = await solana_client.get_balance(pubkey)
            return resp.value / 1_000_000_000
        except: return 0.0

    async def send_report(self, is_alert=False):
        s_bal = await self.get_balance(self.seed_kp.pubkey())
        j_bal = await self.get_balance(self.jito_kp.pubkey())
        msg = (
            f"<b>{'🚨 ALERT' if is_alert else '📊 S.I.P. STATUS'}</b>\n\n"
            f"💰 <b>Seed:</b> <code>{s_bal:.4f} SOL</code>\n"
            f"⚡ <b>Jito:</b> <code>{j_bal:.4f} SOL</code>\n"
            f"🛡️ <b>Security:</b> {'ON' if RUGCHECK_API_KEY else 'OFF'}\n"
            f"-------------------\n"
            f"Mode: {'🟢 HUNTING' if j_bal > self.threshold else '🔴 STANDBY'}"
        )
        try: bot.send_message(ADMIN, msg)
        except Exception as e: logger.error(f"Telegram Fail: {e}")

# --- COMMANDS ---
@bot.message_handler(commands=['start', 'status', 'balance'])
def handle_commands(message):
    if str(message.from_user.id) != ADMIN: return
    sip = SIP_Controller()
    # Runs the async balance check in a one-off loop
    report = asyncio.run(sip.send_report())

# --- MAIN LOOP ---
async def main():
    sip = SIP_Controller()
    await sip.send_report() # Initial ping
    
    # Start Telegram Listener in a background task
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, bot.infinity_polling)
    
    cycle = 0
    while True:
        try:
            if cycle % 60 == 0 and cycle != 0:
                logger.info(f"Heartbeat | Cycle {cycle}")
                # Check for low Jito funds every hour
                j_bal = await sip.get_balance(sip.jito_kp.pubkey())
                if j_bal < sip.threshold: await sip.send_report(is_alert=True)
            
            cycle += 1
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
