import os, asyncio, base58, httpx, logging, time
from decimal import Decimal
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from spl.token.instructions import close_account, CloseAccountParams
from spl.token.constants import TOKEN_PROGRAM_ID

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("SIP_MAINNET_V6")

# --- CONFIG ---
RPC_URL = os.environ.get("RPC_URL")
PRIV_KEY_STR = os.environ.get("PRIVATE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")

# Initialize Keypair & Client
payer = Keypair.from_base58_string(PRIV_KEY_STR)
client = AsyncClient(RPC_URL)

async def send_tg(msg):
    async with httpx.AsyncClient() as h:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            await h.post(url, json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except: pass

async def reclaim_dust():
    """REAL DUST SCRAPING: Reclaiming 0.00204 SOL per empty account"""
    try:
        # FIX: Explicitly use TokenAccountOpts class to avoid AttributeError
        opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
        resp = await client.get_token_accounts_by_owner(payer.pubkey(), opts)
        
        accounts = resp.value
