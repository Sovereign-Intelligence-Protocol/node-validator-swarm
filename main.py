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
logger = logging.getLogger("SIP_REVENUE_PHASE")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# Revenue Tracking
session_revenue = 0.0 

async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance check failed: {e}")
        return 0.0

async def main_engine():
    global session_revenue
    logger.info("🚀 S.I.P. Engine: Revenue Phase 2 Active")
    
    try:
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        # FIX: Ensure pubkey is a string for the startup message
        pub_str = str(pubkey)
        
        bal = await get_balance(pubkey)
        startup_msg = (
            f"💰 <b>Revenue Phase 2: Online</b>\n"
            f"🛡️ Wallet: <code>{pub_str[:6]}...{pub_str[-4:]}</code>\n"
            f"📈 Hunting Status: ACTIVE"
        )
        bot.send_message(ADMIN, startup_msg)

    except Exception as e:
        logger.error(f"❌ Startup Error: {e}")
        return

    # Fix for potential missing attribute
    bot.last_update_id = None
    cycle = 0
    
    while True:
        try:
            # 1. THE REVENUE & HUNTING LOOP (Runs every ~2 seconds)
            if cycle % 1800 == 0 and cycle != 0: # Approx every hour
                current_bal = await get_balance(pubkey)
                bot.send_message(ADMIN, f"📊 <b>Hourly Report</b>\n💰 Wallet: {current_bal:.4f} SOL\n💵 Session Rev: {session_revenue:.4f} SOL")

            # 2. THE COMMAND LISTENER (Safe Non-Blocking)
            updates = bot.get_updates(offset=(bot.last_update_id + 1 if bot.last_update_id else None), timeout=1)
            for update in updates:
                bot.last_update_id = update.update_id
                if update.message and str(update.message.from_user.id) == str(ADMIN):
                    cmd = update.message.text
                    
                    if cmd in ['/health', '/status']:
                        bal = await get_balance(pubkey)
                        bot.reply_to(update.message, f"🟢 <b>System Healthy</b>\n💰 Balance: {bal:.4f} SOL")
                    
                    elif cmd == '/revenue':
                        bot.reply_to(update.message, f"💵 <b>Revenue Report</b>\nTotal Session: {session_revenue:.4f} SOL\nSettlement: Kraken Internal")

            cycle += 1
            await asyncio.sleep(2) 
            
        except Exception as e:
            # Log error but KEEP THE LOOP RUNNING
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_engine())
