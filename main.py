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
logger = logging.getLogger("SIP_ACTIVE")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance check failed: {e}")
        return 0.0

async def main_engine():
    logger.info("🚀 S.I.P. Engine: Active Hunting + Health Check")
    
    try:
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        
        # Initial Startup Notification
        bal = await get_balance(pubkey)
        startup_msg = f"✅ <b>S.I.P. Active</b>\n💰 Balance: <code>{bal:.4f} SOL</code>\n📡 Health Check: Online"
        bot.send_message(ADMIN, startup_msg)

    except Exception as e:
        logger.error(f"❌ Startup Error: {e}")
        return

    cycle = 0
    while True:
        try:
            # 1. THE REVENUE LOOP (The Pulse)
            if cycle % 30 == 0 and cycle != 0:
                current_bal = await get_balance(pubkey)
                bot.send_message(ADMIN, f"📊 <b>Heartbeat Status</b>\n💰 Balance: {current_bal:.4f} SOL")

            # 2. THE HEALTH CHECK LISTENER (Low Impact)
            updates = bot.get_updates(offset=(bot.last_update_id + 1 if bot.last_update_id else None), timeout=1)
            for update in updates:
                bot.last_update_id = update.update_id
                if update.message and str(update.message.from_user.id) == ADMIN:
                    if update.message.text in ['/health', '/status']:
                        current_bal = await get_balance(pubkey)
                        bot.reply_to(update.message, f"🟢 <b>System Healthy</b>\n💰 Current: {current_bal:.4f} SOL\n⏱️ Cycle: {cycle}")

            cycle += 1
            await asyncio.sleep(2) # Faster cycles for better command response without high CPU
            
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_engine())
