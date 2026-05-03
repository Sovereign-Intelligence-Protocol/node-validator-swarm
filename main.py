import os, asyncio, httpx, base58
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- CONFIG ---
RPC = os.getenv("RPC_URL")
KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

app = Flask(__name__)

async def get_wallet_balance():
    """Fetches JitoSOL balance and calculates SOL value."""
    try:
        async with AsyncClient(RPC) as client:
            # Reconstruct your wallet from the private key
            kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
            pubkey = kp.pubkey()
            
            # 1. Get JitoSOL Balance
            resp = await client.get_token_accounts_by_owner(
                pubkey, 
                {"mint": Pubkey.from_string(JITOSOL_MINT)},
                encoding="jsonParsed"
            )
            
            if not resp.value:
                return f"Wallet: `{pubkey[:6]}...`\nBalance: 0 JitoSOL"

            amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
            
            # 2. Get Real-time Price from Jupiter
            async with httpx.AsyncClient() as session:
                p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
                price_data = p_resp.json().get('data', {}).get(JITOSOL_MINT, {})
                sol_val = float(price_data.get('price', 0))

            total_sol = amount * sol_val
            return (
                f"💰 *OMNICORE BALANCE REPORT*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Account: `{pubkey[:8]}...`\n"
                f"Holding: `{amount:.4f} JitoSOL`\n"
                f"Value: `{total_sol:.4f} SOL`"
            )
    except Exception as e:
        return f"Balance Error: {str(e)}"

async def send_tg_report():
    report = await get_wallet_balance()
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": TG_CHAT_ID, "text": report, "parse_mode": "Markdown"})

@app.route('/')
def health():
    # This triggers the balance report to your phone on every Render ping
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_tg_report())
    return "OMNICORE: REPORT SENT", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
