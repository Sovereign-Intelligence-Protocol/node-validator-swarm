import os, asyncio, httpx, base58
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
JITOSOL_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

app = Flask(__name__)

async def get_audit_report():
    """Fetches real-time numbers from the chain."""
    async with AsyncClient(RPC_URL) as client:
        kp = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY.strip()))
        pubkey = kp.pubkey()
        
        # Get JitoSOL balance
        resp = await client.get_token_accounts_by_owner(
            pubkey, {"mint": Pubkey.from_string(JITOSOL_MINT)}, encoding="jsonParsed"
        )
        amount = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount'] if resp.value else 0
        
        # Get Price
        async with httpx.AsyncClient() as session:
            p_resp = await session.get(f"https://api.jup.ag/price/v2?ids={JITOSOL_MINT}")
            price = float(p_resp.json().get('data', {}).get(JITOSOL_MINT, {}).get('price', 0))

        return (
            f"📊 *OMNICORE AUDIT*\n"
            f"Holding: `{amount:.6f} JitoSOL`\n"
            f"Value: `${(amount * price):.2f} USD`"
        )

@app.route('/')
def trigger_report():
    """Render hits this to check if bot is alive. We use it to send the report."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 1. Get the data
        report_text = loop.run_until_complete(get_audit_report())
        
        # 2. Clear old sessions and send (Fixes the 409 Conflict)
        async def send():
            async with httpx.AsyncClient() as client:
                await client.get(f"https://api.telegram.org/bot{TG_TOKEN}/deleteWebhook?drop_pending_updates=True")
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                await client.post(url, json={"chat_id": TG_CHAT_ID, "text": report_text, "parse_mode": "Markdown"})
        
        loop.run_until_complete(send())
        loop.close()
        return "AUDIT SENT", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)
