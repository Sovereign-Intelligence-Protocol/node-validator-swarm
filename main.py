import os
import asyncio
import logging
import requests
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from telegram import Bot

# --- CONFIGURATION (Must match your Render Environment EXACTLY) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")        # Your 8736... API Key
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")              # Your numerical User ID
SEED_WALLET_PK = os.getenv("SOLANA_PRIVATE_KEY")        # Seed Wallet (0.365 SOL)
JITO_SIGNER_PK = os.getenv("JITO_SIGNER_PRIVATE_KEY")   # Jito Signer Key
RUGCHECK_API_KEY = os.getenv("RUGCHECK_API_KEY")       # Security API Key
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Initialize Infrastructure
solana_client = AsyncClient(RPC_URL)
tg_bot = Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Engine")

class SIP_Controller:
    def __init__(self):
        try:
            # Derived Infrastructure
            self.seed_keypair = Keypair.from_base58_string(SEED_WALLET_PK)
            self.jito_keypair = Keypair.from_base58_string(JITO_SIGNER_PK)
            self.threshold = 0.01  # Emergency alert if Jito Signer < 0.01 SOL
            logger.info(f"✅ Infrastructure Verified. Seed Address: {self.seed_keypair.pubkey()}")
        except Exception as e:
            logger.error(f"❌ CRITICAL CONFIG ERROR: {e}")
            raise

    # 1. SECURITY FILTER (RugCheck.xyz)
    async def rug_check_passed(self, mint_address):
        if not RUGCHECK_API_KEY: 
            logger.warning("⚠️ RugCheck key missing! Skipping security check.")
            return True 
        
        url = f"https://api.rugcheck.xyz/v1/tokens/{mint_address}/report"
        headers = {"Authorization": f"Bearer {RUGCHECK_API_KEY}"}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            score = data.get('score', 0)
            if score > 500:
                logger.warning(f"🚨 RUG DETECTED: {mint_address} (Score: {score})")
                return False
            return True
        except Exception as e:
            logger.error(f"⚠️ RugCheck API unavailable: {e}")
            return False # Safety: if we can't verify it, we don't buy it.

    # 2. HEALTH & BALANCE MONITORING
    async def get_sol_balance(self, pubkey):
        try:
            resp = await solana_client.get_balance(pubkey)
            return resp.value / 1_000_000_000
        except: 
            return 0.0

    async def send_status_report(self, is_alert=False):
        seed_bal = await self.get_sol_balance(self.seed_keypair.pubkey())
        jito_bal = await self.get_sol_balance(self.jito_keypair.pubkey())
        
        status_emoji = "🚨 SYSTEM ALERT" if is_alert else "📊 S.I.P. STATUS"
        message = (
            f"<b>{status_emoji}</b>\n\n"
            f"💰 <b>Seed Wallet:</b> {seed_bal:.4f} SOL\n"
            f"⚡ <b>Jito Signer:</b> {jito_bal:.4f} SOL\n"
            f"🛡️ <b>RugCheck:</b> {'ACTIVE' if RUGCHECK_API_KEY else 'OFF'}\n"
            f"-------------------\n"
            f"Status: {'🟢 ACTIVE HUNTING' if jito_bal > self.threshold else '🔴 TOP-UP REQUIRED'}"
        )
        try:
            await tg_bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"❌ Telegram Send Failed (Check Token/ID): {e}")

    # 3. THE MAIN ENGINE
    async def run_hunt(self):
        # Immediate report on startup to verify fixed connection
        await self.send_status_report()
        iteration = 0
        
        while True:
            try:
                # [SCANNING LOGIC]
                logger.info(f"[SCAN] Cycle {iteration}: Monitoring DEX pools...")
                
                # Hourly Balance Heartbeat
                if iteration % 60 == 0 and iteration != 0:
                    jito_bal = await self.get_sol_balance(self.jito_keypair.pubkey())
                    if jito_bal < self.threshold:
                        await self.send_status_report(is_alert=True)
                
                # Daily Comprehensive Status
                if iteration % 1440 == 0 and iteration != 0:
                    await self.send_status_report()

                iteration += 1
                await asyncio.sleep(60) 
            except Exception as e:
                logger.error(f"Runtime Exception: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    sip = SIP_Controller()
    asyncio.run(sip.run_hunt())
