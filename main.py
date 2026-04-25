import os
import asyncio
import logging
import requests
from solders.keypair import Keypair

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_DIAGNOSTIC")

# 1. Grab Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
KEY_STR = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

async def diagnostic_run():
    logger.info("🕵️ Starting Final Diagnostic...")
    
    # TEST 1: Raw Web Request to Telegram
    # This checks if the token is even alive on Telegram's servers
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logger.info("✅ TOKEN IS VALID: Telegram recognizes this bot.")
            # If valid, try to send the message
            send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": ADMIN, "text": "🚀 Diagnostic Success: The Engine is Primed."}
            requests.post(send_url, json=payload)
        else:
            logger.error(f"❌ TOKEN IS INVALID: Telegram returned {response.status_code}. You need a new token from BotFather.")
    except Exception as e:
        logger.error(f"❌ Connection Error: {e}")

    # TEST 2: Wallet Check (We already know this works based on your logs)
    if KEY_STR:
        kp = Keypair.from_base58_string(KEY_STR)
        logger.info(f"✅ Wallet Active: {kp.pubkey()}")

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(diagnostic_run())
