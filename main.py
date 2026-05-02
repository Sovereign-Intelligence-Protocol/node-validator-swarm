import os, threading, asyncio
from flask import Flask

# --- 1. HEARTBEAT SETUP ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Omnicore Live", 200

def run_heartbeat():
    try:
        # Render provides this PORT; default to 10000 for local testing
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Heartbeat Error: {e}")

# Start the thread BEFORE the main logic
threading.Thread(target=run_heartbeat, daemon=True).start()

# --- 2. YOUR MAIN BOT LOGIC ---
async def main_logic():
    print("🚀 S.I.P. Omnicore logic starting...")
    # Add your existing Telegram/Solana loop here
    while True:
        await asyncio.sleep(120) # 120s Heartbeat for Render persistence

if __name__ == "__main__":
    try:
        asyncio.run(main_logic())
    except KeyboardInterrupt:
        pass
