import asyncio
import os
from flask import Flask

# The Heartbeat for Render
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Predator Online", 200

async def start_bot():
    print("--- Canon Initializing ---")
    vault = os.getenv("VAULT_ADDRESS")
    print(f"Targeting Vault: {vault}")
    
    # Your Sniper/Trading Logic goes here
    while True:
        print("Heartbeat: Scanning Solana Network...")
        await asyncio.sleep(60)

def main():
    # This is the specific fix for the 'No current event loop' error
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start the Flask heartbeat in the background
        from threading import Thread
        Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))).start()
        
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"Operational Failure: {e}")

if __name__ == "__main__":
    main()
