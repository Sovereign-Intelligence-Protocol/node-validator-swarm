import os, time, logging, telebot, psycopg2, psutil, backoff
from psycopg2 import pool
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# 1. LOGGING & IDENTITY
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_OMNI_FINAL")

# 2. THE 22-VARIABLE SYNC (MAPPED FROM RENDER)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
DATABASE_URL = os.getenv('DATABASE_URL')
RPC_BASE = os.getenv('SOLANA_RPC_URL_BASE')
RPC_ALT = os.getenv('SOLANA_RPC_URL')
WSS_URL = os.getenv('WSS_URL')
HELIUS_KEY = os.getenv('HELIUS_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
WALLET = os.getenv('SOLANA_WALLET_ADDRESS', 'junTtoquNLdo4PFeC7JbH6Mzj7aztaTckK4dQnZ3')
PRI_KEY = os.getenv('SOLANA_PRIVATE_KEY')
JITO_SIGNER = os.getenv('JITO_SIGNER_PRIVATE_KEY')
JITO_TIP = os.getenv('JITO_TIP_AMOUNT', '0.0001')
LIVE = os.getenv('LIVE_TRADING', 'False').lower() == 'true'
CONFIDENCE = os.getenv('CONFIDENCE_THRESHOLD', '0.9')
MIN_LIQ = os.getenv('MIN_LIQUIDITY_SOL', '10')
MAX_HOLD = os.getenv('MAX_HOLDER_PCT', '5')
RENT_GUARD = os.getenv('RENT_GUARD_THRESHOLD', '0.05')
MASTER_REF = os.getenv('MASTER_REFERRAL_LINK')
POLL_TIME = int(os.getenv('BOT_POLL_TIMEOUT', '90'))
LONG_POLL = int(os.getenv('BOT_LONG_POLL', '40'))
RETRY_SEC = int(os.getenv('BOT_RETRY_DELAY', '10'))

# 3. INFRASTRUCTURE: DB POOLING
try:
    db_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL, sslmode='require')
    logger.info("✅ Database Pool Established.")
except Exception as e:
    logger.error(f"❌ DB Pool Error: {e}")
    db_pool = None

# 4. INITIALIZE CLIENTS
bot = telebot.TeleBot(TOKEN, threaded=False)
solana_client = Client(RPC_BASE or RPC_ALT, commitment="processed")

# 5. COMMANDS
@bot.message_handler(commands=['health'])
def handle_health(message):
    rpc_status = "❌"
    try:
        resp = solana_client.get_block_height()
        h = resp.value if hasattr(resp, 'value') else resp
        rpc_status = f"✅ ({h})"
    except: pass
    
    bot.reply_to(message, (
        "🛰️ *S.I.P. v5.5 OMNI-SYNC*\n"
        f"RPC: {rpc_status} | DB: `{'✅' if db_pool else '❌'}`\n"
        f"Memory: `{psutil.Process(os.getpid()).memory_info().rss // 1024 // 1024}MB` | Live: `{LIVE}`"
    ), parse_mode='Markdown')

@bot.message_handler(commands=['revenue'])
def handle_revenue(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    conn, total = None, 7.01
    if db_pool:
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT total_rev FROM revenue_db_gv0f LIMIT 1;")
                row = cur.fetchone()
                if row: total = row[0]
        finally:
            if conn: db_pool.putconn(conn)
    bot.reply_to(message, f"📊 *Total Revenue:* `{total} SOL` \n🔗 `{MASTER_REF}`", parse_mode='Markdown')

# 6. IGNITION
if __name__ == "__main__":
    try:
        # Standard clean boot
        bot.remove_webhook()
        bot.get_updates(offset=-1, timeout=1)
        
        logger.info(f"🚀 S.I.P. v5.5 IGNITED | WALLET: {WALLET[:6]}")
        
        # Fixed: No duplicate 'non_stop' argument here
        bot.infinity_polling(
            timeout=POLL_TIME, 
            long_polling_timeout=LONG_POLL
        )
    except Exception as e:
        logger.error(f"FATAL: {e}")
        time.sleep(RETRY_SEC)
