import os
import asyncio
import logging
import telebot
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# Minimal Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_TEST")

# 1. Grab Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN = os.getenv("TELEGRAM_ADMIN_ID")
KEY_STR = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

# 2. Immediate Crash Check
if not TOKEN or not ADMIN:
    logger.error("❌ CRITICAL: TOKEN or ADMIN_ID is MISSING in Render.")
    exit(1)

# 3. Initialize Bot WITHOUT management calls
bot = telebot.TeleBot(TOKEN)

async def test_startup():
    logger.info("📡 Testing Telegram connection...")
    try:
        # We don't remove webhooks, we don't set commands. 
        # We just try to send ONE message.
        bot.send_message(ADMIN, "🤖 S.I.P. Engine: Bare Metal Test Started.")
        logger.info("✅ Telegram Message Sent Successfully!")
    except Exception as e:
        logger.error(f"❌ TELEGRAM FAILED: {e}")
        # If this fails with 404, the TOKEN is definitely being read incorrectly by Render.

    try:
        if KEY_STR:
            kp = Keypair.from_base58_string(KEY_STR)
            logger.info(f"✅ Wallet Loaded: {kp.pubkey()}")
        else:
            logger.warning("⚠️ No Wallet Key found.")
    except Exception as e:
        logger.error(f"❌ Wallet Loading Failed: {e}")

    logger.info("🚀 Entering Heartbeat Loop...")
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(test_startup())
