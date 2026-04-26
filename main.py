import os
import asyncio
import logging
import csv
import telebot
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- RENDER PERSISTENT STORAGE CONFIG ---
# Change '/var/data' to whatever your 'Mount Path' is in the Render Disks tab
DATA_DIR = "/var/data" 
REF_FILE = os.path.join(DATA_DIR, "referrals.csv")

# Ensure the directory exists (prevents crashes if disk isn't mounted)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# --- STANDARD CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_PHASE_3_PERSISTENT")
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
solana_client = AsyncClient(RPC_URL)

session_revenue = 0.0

def log_referral(user_id, referrer_id):
    """Saves referral data to the PERSISTENT DISK"""
    file_exists = os.path.isfile(REF_FILE)
    try:
        with open(REF_FILE, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'New_User', 'Referrer'])
            writer.writerow([datetime.now(), user_id, referrer_id])
    except Exception as e:
        logger.error(f"Failed to write to disk: {e}")

async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance check failed: {e}")
        return 0.0

async def main_engine():
    global session_revenue
    logger.info(f"🚀 S.I.P. Persistent Mode: Writing to {REF_FILE}")
    
    try:
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        pub_str = str(pubkey)
        
        bal = await get_balance(pubkey)
        bot.send_message(ADMIN, f"🛰️ <b>Phase 3+ (Storage Active)</b>\n🛡️ Wallet: <code>{pub_str[:6]}...</code>\n📂 Disk Path: <code>{DATA_DIR}</code>")
    except Exception as e:
        logger.error(f"Startup Error: {e}")
        return

    bot.last_update_id = None
    cycle = 0
    
    while True:
        try:
            if cycle % 1800 == 0 and cycle != 0:
                current_bal = await get_balance(pubkey)
                bot.send_message(ADMIN, f"📊 <b>Hourly Report</b>\n💰 Wallet: {current_bal:.4f} SOL")

            updates = bot.get_updates(offset=(bot.last_update_id + 1 if bot.last_update_id else None), timeout=1)
            for update in updates:
                bot.last_update_id = update.update_id
                if not update.message: continue
                
                uid = str(update.message.from_user.id)
                text = update.message.text or ""

                if text.startswith('/start') and len(text.split()) > 1:
                    referrer = text.split()[1]
                    if referrer != uid:
                        log_referral(uid, referrer)
                        bot.reply_to(update.message, "🎟️ <b>Toll Bridge Activated</b>")
                        bot.send_message(ADMIN, f"🔔 <b>New Referral Saved to Disk</b>\nReferrer: <code>{referrer}</code>")

                if uid == str(ADMIN):
                    if text in ['/health', '/status']:
                        bal = await get_balance(pubkey)
                        bot.reply_to(update.message, f"🟢 <b>System Healthy</b>\n💰 Balance: {bal:.4f} SOL")
                    
                    elif text == '/revenue':
                        try:
                            with open(REF_FILE, 'r') as f:
                                ref_count = sum(1 for line in f) - 1
                        except: ref_count = 0
                        bot.reply_to(update.message, f"💵 <b>Revenue Report</b>\nTotal Referrals (Saved): {ref_count}")

            cycle += 1
            await asyncio.sleep(2) 
            
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_engine())
