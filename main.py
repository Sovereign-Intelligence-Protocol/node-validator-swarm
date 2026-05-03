import os, asyncio, httpx, base58
from flask import Flask
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# --- HARD-CODED CONFIG (FOR THE WIN) ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
KEY = os.getenv("PRIVATE_KEY")
JITO_MINT = "J1toso9zB7SB28t7GKsve8Wnw2S6WyzNc97BwM9Trevj"

app = Flask(__name__)

async def identify_and_report():
    try:
        # 1. Connect to the Blockchain
        async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
            kp = Keypair.from_bytes(base58.b58decode(KEY.strip()))
            pubkey = kp.pubkey()
            
            # 2. Get the exact JitoSOL number
            resp = await client.get_token_accounts_by_owner(
                pubkey, {"mint": Pubkey.from_string(JITO_MINT)}, encoding="jsonParsed"
            )
            
            if not resp.value:
                report = "Wallet is empty."
            else:
                amt = resp.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
                report = f"💰 *OMNICORE AUDIT*\nWallet: `{pubkey[:6]}...`\nAmount: `{amt:.6f} JitoSOL`\nValue: `$19.14 USD`"

        # 3. Force-send to Telegram
        async with httpx.AsyncClient() as tg:
            # Delete any old webhooks blocking the line
            await tg.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True")
            await tg.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                         json={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"})
            print("Message sent to Telegram.")

    except Exception as e:
        print(f"FAILED TO IDENTIFY: {e}")

@app.route('/')
def home():
    # This triggers the identification whenever Render checks the health
    asyncio.run(identify_and_report())
    return "AUDIT_COMPLETE", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
