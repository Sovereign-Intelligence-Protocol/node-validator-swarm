import os
import asyncio
import logging
import requests
import telebot
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
SEED_WALLET_PK = os.getenv("SOLANA_PRIVATE_KEY")
JITO_SIGNER_PK = os.getenv("JITO_SIGNER_PRIVATE_KEY")
RUGCHECK_API_KEY = os.getenv("RUGCHECK_API_KEY")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Initialize Infrastructure
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')
solana_client = AsyncClient(RPC_URL)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Engine")

class SIP_Controller:
    def __init__(self):
        try:
            # Setup Keypairs
            self.seed_kp = Keypair.from_base58_string(SEED_WALLET_PK)
            self.jito_kp = Keypair.from_base58_string(JITO_SIGNER_PK)
            self.threshold = 0.01 
            
            # Remove Webhooks to eliminate the 404 Error
            bot.remove_webhook()
            logger.info(f"✅ S.I.P. LOADED | Seed Address: {self.seed_kp.pubkey()}")
        except Exception as e:
            logger.error(f"❌ Initialization Fail: {e}")
            raise

    async def get_balance(self, pubkey):
        try:
            r = await solana_client.get_balance(pubkey)
            return r.value / 1_000_000_000
        except Exception: 
            return 0.0

    async def send_status_report(self, alert=False):
        s_bal = await self.get_balance(self.seed_kp.pubkey())
        j_bal = await self.get_balance(self.jito_kp.pubkey())
        
        status_emoji = "🚨 ALERT" if alert else "📊 S.I.P. STATUS"
        msg = (
            f"<b>{status_emoji}</b>\n\n"
            f"💰 <b>Seed Wallet:</b> {s_bal:.4f} SOL\n"
            f"⚡ <b>Jito Signer:</b> {j_bal:.4f} SOL\n"
            f"🛡️ <b>RugCheck API:</b> {'CONNECTED' if RUGCHECK_API_KEY else 'OFFLINE'}\n"
            f"-------------------\n"
            f"Mode: {'🟢 ACTIVE HUNTING' if j_bal > self.threshold else '🔴 STANDBY - REFILL'}"
        )
        try:
            bot.send_message(ADMIN_ID, msg)
        except Exception as e:
            logger.error(f"Telegram Notification Failed: {e}")

    async def check_rug_security(self, mint_address):
        """Programmatic RugCheck audit before any trade."""
        if not RUGCHECK_API_KEY: 
            return True
        try:
            url = f"https://api.rugcheck.xyz/v1/tokens/{mint_address}/report"
            headers = {"Authorization": f"Bearer {RUGCHECK_API_KEY}"}
            res = requests.get(url, headers=headers, timeout=5)
            score = res.json().get('score', 0)
            if score > 500:
                logger.warning(f"🚨 SKIP: {mint_address} is too risky (Score: {score})")
                return False
            return True
        except: 
            return False

    async def run_engine(self):
        # Immediate confirmation that the bot is alive and 404 is fixed
        await self.send_status_report()
        cycle = 0
        while True:
            try:
                # [CORE OPERATION]
                logger.info(f"[SIP] Cycle {cycle}: Monitoring Solana Mainnet...")
                
                # Hourly Balance Heartbeat
                if cycle % 60 == 0 and cycle != 0:
                    j_bal = await self.get_balance(self.jito_kp.pubkey())
                    if j_bal < self.threshold: 
                        await self.send_status_report(alert=True)
                
                # Daily Status Report
                if cycle % 1440 == 0 and cycle != 0: 
                    await self.send_status_report()

                cycle += 1
                await asyncio.sleep(60) 
            except Exception as e:
                logger.error(f"Runtime Loop Error: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    sip = SIP_Controller()
    asyncio.run(sip.run_engine())
