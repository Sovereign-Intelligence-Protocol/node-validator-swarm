import os, threading
from flask import Flask

# 1. Create the 'Heartbeat' to stop the 60s Render loop
app = Flask(__name__)

@app.route('/')
def health():
    return "Omnicore Live", 200

def run_heartbeat():
    # Render assigns a dynamic port via environment variables
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Start the heartbeat in a background thread
threading.Thread(target=run_heartbeat, daemon=True).start()

# --- Rest of your original bot code starts here ---
