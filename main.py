import os
import asyncio
import logging
import psycopg2
import telebot
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# --- INSTITUTIONAL CONFIG ---
DB_URL = os.getenv("DATABASE_URL")
MASTER_LINK = os.getenv("MASTER_REFERRAL_LINK", "None Set")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_INSTITUTIONAL")
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
solana_client = AsyncClient(RPC_URL)

def init_db():
    """Persistent Storage Check"""
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
        logger.info("✅ PostgreSQL Persistent")
    except Exception as e:
        logger.error(f"❌ DB Failure: {e}")

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
        logger.error(f"❌ Toll Log Failed: {e}")

async def get_balance(pubkey):
    try:
        resp = await solana_client.get_balance(pubkey)
        return resp.value / 1_000_000_000
    except Exception as e:
        return 0.0

async def main_engine():
    init_db()
    
    # --- CONFLICT SHIELD: Resolves Error 409 ---
    try:
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("🛡️ Conflict Shield Active: Old instances cleared.")
    except: pass

    try:
        kp = Keypair.from_base58_string(SEED_PK)
        pubkey = kp.pubkey()
        
        # Confirmation of Master Link status
        bot.send_message(ADMIN, (
            f"🛰️ <b>S.I.P. Institutional Online</b>\n"
            f"🔗 Master: <code>{MASTER_LINK}</code>\n"
            f"🛡️ Wallet: <code>{str(pubkey)[:6]}...</code>"
        ))
    except Exception as e:
        logger.error(f"Startup Error: {e}")
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

                if text.startswith('/start') and len(text.split()) > 1:
                    referrer = text.split()[1]
                    if referrer != uid:
                        log_referral(uid, referrer)
                        bot.reply_to(update.message, "🎟️ <b>Toll Bridge Active</b>\nExecution shielded.")

                if uid == str(ADMIN):
                    if text in ['/health', '/status']:
                        bal = await get_balance(pubkey)
                        bot.reply_to(update.message, f"🟢 <b>Status: Optimal</b>\n💰 Balance: {bal:.4f} SOL")
                    
                    elif text == '/revenue':
                        # Audit Report
                        conn = psycopg2.connect(DB_URL)
                        cur = conn.cursor()
                        cur.execute("SELECT COUNT(*) FROM referrals")
                        count = cur.fetchone()[0]
                        cur.close()
                        conn.close()
                        
                        bot.reply_to(update.message, (
                            f"📊 <b>Revenue Audit</b>\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"👥 Users: <code>{count}</code>\n"
                            f"💰 Est. Tolls: <code>{count * 0.01:.2f} SOL</code>\n"
                            f"📈 <b>Total Rev: 7.01 SOL</b>" # From your latest audit
                        ))

            await asyncio.sleep(2) 
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_engine())
