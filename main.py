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
MASTER_LINK = os.getenv("MASTER_REFERRAL_LINK", "Variable Not Found")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_FINAL_AUDIT")
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
solana_client = AsyncClient(RPC_URL)

def init_db():
    """Double-checked: Ensures table existence without overwriting data"""
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
        logger.info("✅ Database verified.")
    except Exception as e:
        logger.error(f"❌ DB Check failed: {e}")

def log_referral(user_id, referrer_id):
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
        logger.error(f"❌ Logging failed: {e}")

async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except Exception as e:
        logger.error(f"Balance check error: {e}")
        return 0.0

async def main_engine():
    init_db()
    
    try:
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        pub_str = str(pubkey)
        
        # Initial Heartbeat
        bot.send_message(ADMIN, f"🛰️ <b>S.I.P. Institutional: Online</b>\n🔗 Master Link: <code>{MASTER_LINK}</code>\n🛡️ Wallet: <code>{pub_str[:6]}...</code>")
    except Exception as e:
        logger.error(f"Critical Startup Failure: {e}")
        return

    bot.last_update_id = None
    
    while True:
        try:
            updates = bot.get_updates(offset=(bot.last_update_id + 1 if bot.last_update_id else None), timeout=1)
            for update in updates:
                bot.last_update_id = update.update_id
                if not update.message: continue
                
                uid = str(update.message.from_user.id)
                text = update.message.text or ""

                # Referral Logic
                if text.startswith('/start') and len(text.split()) > 1:
                    referrer = text.split()[1]
                    if referrer != uid:
                        log_referral(uid, referrer)
                        bot.reply_to(update.message, "🎟️ <b>Toll Bridge: Access Granted</b>\nShielding active for this session.")
                        bot.send_message(ADMIN, f"🔔 <b>New Referral</b>\nID: <code>{referrer}</code>")

                # Admin Logic
                if uid == str(ADMIN):
                    if text in ['/health', '/status']:
                        bal = await get_balance(pubkey)
                        bot.reply_to(update.message, f"🟢 <b>Status: Optimal</b>\n💰 Balance: {bal:.4f} SOL")
                    
                    elif text == '/revenue':
                        try:
                            conn = psycopg2.connect(DB_URL)
                            cur = conn.cursor()
                            cur.execute("SELECT COUNT(*) FROM referrals")
                            ref_count = cur.fetchone()[0]
                            cur.close()
                            conn.close()
                            
                            bot.reply_to(update.message, (
                                f"📊 <b>Revenue Snapshot</b>\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"👥 Active Users: <code>{ref_count}</code>\n"
                                f"💰 Est. Tolls: <code>{ref_count * 0.01:.2f} SOL</code>\n"
                                f"📈 Growth: <b>Active</b>"
                            ))
                        except Exception as e:
                            bot.reply_to(update.message, "❌ DB Query Failed.")

            await asyncio.sleep(2) 
            
        except Exception as e:
            logger.error(f"Runtime Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_engine())
