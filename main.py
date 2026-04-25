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

# Simple, reliable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_CORE")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TOKEN)

async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except:
        return 0.0

async def main_engine():
    logger.info("🚀 S.I.P. Engine Starting (Reliability Mode)...")
    
    try:
        # Load Wallet
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        logger.info(f"✅ Wallet Active: {pubkey}")
        
        # Initial Startup Notification
        bal = await get_balance(pubkey)
        msg = f"🚀 <b>S.I.P. Engine Online</b>\n\n💰 Balance: <code>{bal:.4f} SOL</code>\n🛡️ Status: Active Hunting"
        bot.send_message(ADMIN, msg, parse_mode='HTML')
        logger.info("✅ Startup message sent to Telegram.")

    except Exception as e:
        logger.error(f"❌ Critical Startup Error: {e}")
        return

    # MAIN LOOP - No threading, no command polling, just pure execution
    cycle = 0
    while True:
        try:
            # Check balance/status every 30 minutes
            if cycle % 30 == 0 and cycle != 0:
                current_bal = await get_balance(pubkey)
                bot.send_message(ADMIN, f"📊 <b>Heartbeat Status</b>\n💰 Balance: {current_bal:.4f} SOL", parse_mode='HTML')
            
            if cycle % 5 == 0:
                logger.info(f"Heartbeat Cycle {cycle} | Wallet: {pubkey}")

            cycle += 1
            await asyncio.sleep(60) # 1 minute cycles
            
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main_engine())
