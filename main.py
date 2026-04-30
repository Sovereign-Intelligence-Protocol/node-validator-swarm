import os, asyncio, base58, httpx, logging
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
logger = logging.getLogger("SIP_CORE")

# --- CONFIG ---
RPC_URL = os.environ.get("RPC_URL")
PRIV_KEY_STR = os.environ.get("PRIVATE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")

# Initialize
payer = Keypair.from_base58_string(PRIV_KEY_STR)
client = AsyncClient(RPC_URL)

async def send_tg(msg):
    async with httpx.AsyncClient() as h:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            await h.post(url, json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except Exception as e:
            logger.error(f"Telegram Error: {e}")

async def reclaim_dust():
    try:
        opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
        resp = await client.get_token_accounts_by_owner(payer.pubkey(), opts)
        
        accounts = resp.value
        reclaimed_count = 0

        for acc in accounts:
            balance_resp = await client.get_token_account_balance(acc.pubkey)
            if balance_resp.value.ui_amount == 0:
                ix = close_account(CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=acc.pubkey,
                    dest=payer.pubkey(),
                    owner=payer.pubkey()
                ))
                
                blockhash = (await client.get_latest_blockhash()).value.blockhash
                
                msg = MessageV0.try_compile(
                    payer=payer.pubkey(),
                    instructions=[ix],
                    address_lookup_table_accounts=[],
                    recent_blockhash=blockhash
                )
                tx = VersionedTransaction(msg, [payer])
                
                send_resp = await client.send_transaction(tx)
                logger.info(f"🔥 DUST RECLAIMED: {send_resp.value}")
                reclaimed_count += 1
                
        return reclaimed_count
    except Exception as e:
        logger.error(f"Scraper Error: {e}")
        return 0

async def master_loop():
    logger.info("🚀 OMNICORE v6.2 ONLINE")
    await send_tg("🚀 <b>OMNICORE v6.2: LIVE ON MAINNET</b>")

    while True:
        try:
            # Main Scavenger Action
            reclaimed = await reclaim_dust()
            if reclaimed > 0:
                await send_tg(f"🔥 <b>RECLAIMED:</b> {reclaimed * 0.00204:.4f} SOL")
        except Exception as e:
            logger.error(f"Loop error: {e}")
            
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(master_loop())
