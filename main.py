import os
import asyncio
import logging
import requests
import telebot
import threading
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
SEED_PK_STR = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
JITO_PK_STR = os.getenv("JITO_SIGNER_PRIVATE_KEY") or os.getenv("JITO_KEY")
RUGCHECK_API_KEY = os.getenv("RUGCHECK_API_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Global Infrastructure
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Final_Engine")
solana_client = AsyncClient(RPC_URL)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')

class SIP_Controller:
    def __init__(self):
        try:
            # 1. HARD RESET TELEGRAM
            bot.remove_webhook(drop_pending_updates=True)
            
            # 2. LOAD KEYPAIRS
            if not SEED_PK_STR:
                raise ValueError("CRITICAL: SOLANA_PRIVATE_KEY is missing.")
            
            self.seed_kp = Keypair.from_base58_string(SEED_PK_STR)
            self.jito_kp = Keypair.from_base58_string(JITO_PK_STR) if JITO_PK_STR else self.seed_kp
            self.alert_threshold = 0.01
            logger.info(f"✅ S.I.P. INITIALIZED | Seed: {self.seed_kp.pubkey()}")
        except Exception as e:
            logger.error(f"❌ STARTUP ERROR: {e}")
            raise

    async def get_sol_balance(self, pubkey):
        try:
            resp = await solana_client.get_balance(pubkey)
            return resp.value / 1_000_000_000
        except: return 0.0

    async def generate_report_text(self, is_alert=False):
        seed_bal = await self.get_sol_balance(self.seed_kp.pubkey())
        jito_bal = await self.get_sol_balance(self.jito_kp.pubkey())
        header = "🚨 ALERT" if is_alert else "📊 S.I.P. STATUS"
        return (
            f"<b>{header}</b>\n\n"
            f"💰 <b>Seed Wallet:</b> <code>{seed_bal:.4f} SOL</code>\n"
            f"⚡ <b>Jito Signer:</b> <code>{jito_bal:.4f} SOL</code>\n"
            f"🛡️ <b>Security Gate:</b> {'ACTIVE' if RUGCHECK_API_KEY else 'OFF'}\n"
            f"-------------------\n"
            f"Status: {'🟢 ACTIVE HUNTING' if jito_bal > self.alert_threshold else '🔴 STANDBY (Refill Required)'}"
        )

# --- TELEGRAM COMMAND HANDLERS ---
@bot.message_handler(commands=['start', 'status', 'balance'])
def handle_commands(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    # Create a temporary loop to handle the async balance check for the command
    temp_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(temp_loop)
    sip = SIP_Controller()
    report = temp_loop.run_until_complete(sip.generate_report_text())
    bot.
