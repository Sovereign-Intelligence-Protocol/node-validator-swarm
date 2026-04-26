import os
import asyncio
import logging
import psycopg2
import telebot
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- CONFIGURATION ---
DB_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_DB_PRO")
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
solana_client = AsyncClient(RPC_URL)

# --- DATABASE LOGIC ---
def init_db():
    """Initializes the persistent referral table"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                user_id TEXT NOT NULL,
                referrer_id TEXT NOT NULL
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ PostgreSQL Initialized")
    except Exception as e:
        logger.error(f"❌ DB Init Error: {e}")

def log_referral(user_id, referrer_id):
    """Saves a new referral to the database"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO referrals (timestamp, user_id, referrer_id) VALUES (%s, %s, %s)",
            (datetime.now(), user_id, referrer_id)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"❌ DB Write Error: {e}")

# --- CORE ENGINE ---
async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance check failed: {e}")
        return 0.0

async def main_engine():
    init_db()
    logger.info("🚀 S.I.P. Engine: Database Phase Active")
    
    try:
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        pub_str = str(pubkey) # Fix for the subscriptable error
        
        bal = await get_balance(pubkey)
        bot.send_message(ADMIN, f"🛰️ <b>S.I.P. DB Phase Online</b>\n🛡️ Wallet: <code>{pub_str[:6]}...</code>\n🗄️ Storage: <b>PostgreSQL Active</b>")
    except Exception as e:
        logger.error(f"Startup Error: {e}")
        return

    bot.last_update_id = None
    cycle = 0
    
    while True:
        try:
            # 1. Hourly Heartbeat
            if cycle % 1800 == 0 and cycle != 0:
                current_bal = await get_balance(pubkey)
                bot.send_message(ADMIN, f"📊 <b>Hourly Report</b>\n💰 Wallet: {current_bal:.4f} SOL")

            # 2. Command & Referral Listener
            updates = bot.get_updates(offset=(bot.last_update_id + 1 if bot.last_update_id else None), timeout=1)
            for update in updates:
                bot.last_update_id = update.update_id
                if not update.message: continue
                
                uid = str(update.message.from_user.id)
                text = update.message.text or ""

                # Handle Referral Link
                if text.startswith('/start') and len(text.split()) > 1:
                    referrer = text.split()[1]
                    if referrer != uid:
                        log_referral(uid, referrer)
                        bot.reply_to(update.message, "🎟️ <b>Toll Bridge Activated</b>")
                        bot.send_message(ADMIN, f"🔔 <b>New Referral Logged to DB</b>\nReferrer: <code>{referrer}</code>")

                # Admin Logic
                if uid == str(ADMIN):
                    if text in ['/health', '/status']:
                        bal = await get_balance(pubkey)
                        bot.reply_to(update.message, f"🟢 <b>System Healthy</b>\n💰 Balance: {bal:.4f} SOL")
                    
                    elif text == '/revenue':
                        try:
                            conn = psycopg2.connect(DB_URL)
                            cur = conn.cursor()
                            cur.execute("SELECT COUNT(*) FROM referrals")
                            ref_count = cur.fetchone()[0]
                            cur.close()
                            conn.close()
                        except: ref_count = "Error"
                        bot.reply_to(update.message, f"💵 <b>Revenue Report</b>\nTotal Database Referrals: {ref_count}")

            cycle += 1
            await asyncio.sleep(2) 
            
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_engine())
