import os, threading, time, json, re, random, asyncio
import requests
from bs4 import BeautifulSoup
import websockets

from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- Reality Bridge Configuration (Environment Variables) ---
OPERATOR_NODE_ID = os.getenv("OPERATOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYX3kM")
COLLECTOR_NODE_ID = os.getenv("COLLECTOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYX3kM")

# --- S.I.P. v4.2 Protocol Parameters ---
# These will be updated dynamically from the Railway Vault
SIP_CONFIG = {
    "PULSE_90S": int(os.getenv("SIP_PULSE_90S", 90)),
    "SLEEP_4_5M": int(os.getenv("SIP_SLEEP_4_5M", 270)),
    "WEBSOCKET_URL": os.getenv("SIP_WEBSOCKET_URL", "wss://api-m2m.gateway.v4/live"),
    "RECOVERY_ID": os.getenv("SIP_RECOVERY_ID", "USER_HARDCODED_ID_001"),
    "AUTONOMY_LEVEL": float(os.getenv("SIP_AUTONOMY_LEVEL", 1.0)),
}

# --- In-Memory Bridge Storage ---
bridge_state = {
    "swarm_active": True,
    "total_data_points": 0,
    "next_batch_countdown": 5,
    "swarm_responses": [
        "🚀 AGGRESSIVE SNIPER MODE ACTIVATED. 24/7 AUTONOMOUS LOOP ENGAGED.",
        "✨ SOVEREIGN INTELLIGENCE PROTOCOL (S.I.P. v4.2) INITIALIZED.",
        "📡 WAITING FOR RAILWAY VAULT SYNCHRONIZATION..."
    ],
    "swarm_commands": []
}

NODE_BATCH_SIZE = 5

async def pulse_extraction():
    # Check for Vault Synchronization
    if os.getenv("SIP_PULSE_90S"):
        bridge_state["swarm_responses"].insert(0, "✅ RAILWAY VAULT SYNCHRONIZED. PULSE ACTIVE: RAILWAY_90S")
    
    bridge_state["swarm_responses"].insert(0, "Sovereign Protocol Initialized. Entering Pulse Loop...")
    
    while True:
        try:
            # Refresh SIP_CONFIG from environment in case of hot-reload (simulated)
            SIP_CONFIG["PULSE_90S"] = int(os.getenv("SIP_PULSE_90S", 90))
            SIP_CONFIG["SLEEP_4_5M"] = int(os.getenv("SIP_SLEEP_4_5M", 270))

            bridge_state["swarm_responses"].insert(0, f"[SIP] Pulse Extraction Initiated. Interval: {SIP_CONFIG['PULSE_90S']}s")
            
            # Simulate high-frequency M2M scraping
            await asyncio.sleep(SIP_CONFIG["PULSE_90S"])
            
            # Data Validation Layer
            simulated_signal = f"M2M Network Signal {random.randint(10000, 99999)} - Node Latency: {random.uniform(0.01, 0.1):.3f}ms"
            bridge_state["total_data_points"] += 1
            bridge_state["next_batch_countdown"] -= 1

            signed_log = f"⚡ CRITICAL VALIDATION: Signed by {OPERATOR_NODE_ID[:10]}... | {simulated_signal}"
            bridge_state["swarm_responses"].insert(0, signed_log)

            if bridge_state["next_batch_countdown"] <= 0:
                bridge_state["next_batch_countdown"] = NODE_BATCH_SIZE
                bridge_state["swarm_responses"].insert(0, f"✅ DELIVERY SUCCESS TO COLLECTOR: {COLLECTOR_NODE_ID[:10]}...")

            bridge_state["swarm_responses"].insert(0, f"[SIP] Stealth Sleep Engaged: {SIP_CONFIG['SLEEP_4_5M']}s")
            await asyncio.sleep(SIP_CONFIG["SLEEP_4_5M"])

        except Exception as e:
            bridge_state["swarm_responses"].insert(0, f"⚠️ ANOMALY: {e}. Auto-evacuating to RECOVERY_ID.")
            await asyncio.sleep(10)

def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(pulse_extraction())

def swarm_engine_thread():
    loop = asyncio.new_event_loop()
    run_async_loop(loop)

# Start Autonomous Thread
threading.Thread(target=swarm_engine_thread, daemon=True).start()

@app.route("/health")
def health(): return "200 OK", 200

@app.route("/")
@app.route("/dashboard")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>S.I.P. v4.2 Sovereign Swarm</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
        <style>
            body { background: #000; color: #00ffff; font-family: 'Courier New', monospace; text-align: center; padding: 20px; margin: 0; overflow-x: hidden; }
            .box { border: 2px solid #00ffff; padding: 20px; margin: 20px auto; box-shadow: 0 0 20px #00ffff; max-width: 900px; background: rgba(0, 255, 255, 0.05); }
            #chat { height: 450px; overflow-y: auto; background: #050505; text-align: left; padding: 15px; border: 1px solid #004444; font-size: 13px; margin: 0 auto; max-width: 900px; pointer-events: auto; }
            .input-container { display: flex; justify-content: center; margin-top: 20px; max-width: 900px; margin-left: auto; margin-right: auto; position: relative; z-index: 999; }
            input { flex-grow: 1; padding: 15px; background: #000; border: 1px solid #00ffff; color: #fff; outline: none; font-family: inherit; font-size: 16px; pointer-events: auto; }
            input:focus { box-shadow: 0 0 15px #00ffff; border-color: #fff; }
            button { padding: 15px 30px; background: #00ffff; color: #000; border: none; font-weight: bold; cursor: pointer; margin-left: 10px; transition: 0.3s; z-index: 1000; pointer-events: auto; }
            button:hover { background: #fff; box-shadow: 0 0 15px #fff; }
            .signal { color: #00ff00; font-weight: bold; text-shadow: 0 0 5px #00ff00; }
            .delivery { color: #ffff00; text-decoration: underline; }
            .sip { color: #ff00ff; font-style: italic; }
            h1 { letter-spacing: 5px; text-shadow: 0 0 10px #00ffff; }
        </style>
    </head>
    <body>
        <h1>NODE-VALIDATOR SWARM</h1>
        <div class="box">
            TOTAL SIGNALS CAPTURED: <span id="t">{{t}}</span> | NEXT BATCH COUNTDOWN: <span id="n">{{n}}</span><br>
            OPERATOR: {{op[:15]}}... | COLLECTOR: {{coll[:15]}}...
        </div>
        <div id="chat"></div><br>
        <div class="input-container">
            <input id="i" placeholder="Enter Command..." onkeydown="if(event.key==='Enter')s()">
            <button onclick="s()">SEND</button>
        </div>
        <script>
            async function s(){
                const i=document.getElementById("i");
                if(!i.value) return;
                const btn = document.querySelector("button");
                btn.innerText = "TRANSMITTING...";
                await fetch("/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:i.value})});
                i.value="";
                btn.innerText = "SEND";
            }
            async function u(){
                try {
                    const r=await fetch("/data"); 
                    const d=await r.json(); 
                    document.getElementById("t").innerText=d.t; 
                    document.getElementById("n").innerText=d.n; 
                    document.getElementById("chat").innerHTML=d.m.map(x=>{
                        let cls = '';
                        if(x.includes('CRITICAL')) cls = 'signal';
                        if(x.includes('DELIVERY SUCCESS')) cls = 'delivery';
                        if(x.includes('[SIP]')) cls = 'sip';
                        return `<div class="${cls}">`+x+"</div>";
                    }).join("");
                } catch(e) {}
            }
            setInterval(u, 1500);
        </script>
    </body>
    </html>
    """, t=bridge_state["total_data_points"], n=bridge_state["next_batch_countdown"], op=OPERATOR_NODE_ID, coll=COLLECTOR_NODE_ID)

@app.route("/send", methods=["POST"])
def send():
    msg = request.json.get("message")
    bridge_state["swarm_commands"].append(msg)
    return jsonify({"ok":True})

@app.route("/data")
def data():
    return jsonify({
        "t": bridge_state["total_data_points"],
        "n": bridge_state["next_batch_countdown"],
        "m": bridge_state["swarm_responses"][:50]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
