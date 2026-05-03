import os, asyncio, httpx
from flask import Flask
from threading import Thread

# --- CONFIG ---
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

async def send_tg_async(text):
    """The actual sender logic."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    async with httpx.AsyncClient() as client:
        try:
            # Drop old updates to prevent the 409 Conflict
            await client.get(f"https://api.telegram.org/bot{TG_TOKEN}/deleteWebhook?drop_pending_updates=True")
            r = await client.post(url, json=payload, timeout=10.0)
            print(f"Telegram API Status: {r.status_code}")
        except Exception as e:
            print(f"Telegram Error: {e}")

@app.route('/')
def health():
    # TRIGGER: When Render pings this URL, it forces the Telegram message
    # We run it in a new loop so it doesn't block the web response
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_tg_async("🎯 *S.I.P. Omnicore: Triggered.* Handshake received via Render Health Check."))
    return "OMNICORE: ONLINE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    # 'threaded=True' allows the health check to trigger the message without crashing
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == "__main__":
    print("Direct Shot Engine Starting...")
    run_flask()
