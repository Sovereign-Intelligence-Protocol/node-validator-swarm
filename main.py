from flask import Flask, render_template_string, request, jsonify
import os, threading, time, json, re, random, csv
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- Reality Bridge Configuration (Environment Variables) ---
OPERATOR_NODE_ID = os.getenv("OPERATOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")
COLLECTOR_NODE_ID = os.getenv("COLLECTOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")

# --- In-Memory Bridge Storage ---
bridge_state = {
    "swarm_active": True,
    "total_data_points": 0,
    "next_batch_countdown": 5,
    "swarm_responses": ["🚀 AGGRESSIVE SNIPER MODE ACTIVATED."],
    "swarm_commands": []
}

NODE_BATCH_SIZE = 5

SNIPER_TARGETS = [
    "blockchain network signal", "node deployment data", "validator status live",
    "p2p network discovery", "network telemetry report", "consensus signal active"
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
]

def scrape_sniper_signals(query):
    data_points = []
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for res in soup.find_all("div", class_="result"):
                title_elem = res.find("a", class_="result__url")
                snippet_elem = res.find("a", class_="result__snippet")
                if title_elem and snippet_elem:
                    link = title_elem.get("href", "N/A")
                    snippet = snippet_elem.text.strip()
                    if any(char.isdigit() for char in snippet) or "node" in snippet.lower():
                        data_points.append([link[:40] + "...", snippet[:80] + "..."])
    except Exception as e:
        print(f"[-] ERROR: {e}")
    return data_points

def swarm_engine():
    target_idx = 0
    while True:
        try:
            if bridge_state["swarm_commands"]:
                cmd = bridge_state["swarm_commands"].pop(0)
                if cmd.startswith("/start-swarm"):
                    bridge_state["swarm_active"] = True
                    bridge_state["swarm_responses"].insert(0, "🎯 SNIPER LOOP RE-ENGAGED.")
                elif cmd.startswith("/stop-swarm"):
                    bridge_state["swarm_active"] = False
                    bridge_state["swarm_responses"].insert(0, "🛑 SNIPER LOOP PAUSED.")

            if bridge_state["swarm_active"]:
                target = SNIPER_TARGETS[target_idx]
                verified_data = scrape_sniper_signals(target)
                if verified_data:
                    for signal_source, signal_data in verified_data:
                        bridge_state["total_data_points"] += 1
                        bridge_state["next_batch_countdown"] -= 1
                        bridge_state["swarm_responses"].insert(0, f"⚡ CRITICAL VALIDATION: {signal_source} | {signal_data}")
                        if bridge_state["next_batch_countdown"] <= 0:
                            bridge_state["next_batch_countdown"] = NODE_BATCH_SIZE
                            bridge_state["swarm_responses"].insert(0, "✅ BATCH FULL: HANDOFF TO COLLECTOR.")
                        if bridge_state["total_data_points"] % 5 == 0: break
                target_idx = (target_idx + 1) % len(SNIPER_TARGETS)
            time.sleep(10)
        except Exception as e:
            time.sleep(10)

threading.Thread(target=swarm_engine, daemon=True).start()

@app.route("/health")
def health(): return "200 OK", 200

@app.route("/")
@app.route("/dashboard")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aggressive Sniper Swarm</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
        <style>
            body { background: #000; color: #ff00ff; font-family: monospace; text-align: center; padding: 20px; margin: 0; overflow: hidden; }
            .box { border: 1px solid #ff00ff; padding: 20px; margin: 20px auto; box-shadow: 0 0 15px #ff00ff; max-width: 90%; }
            #chat { height: 400px; overflow-y: auto; background: #050505; text-align: left; padding: 10px; border: 1px solid #330033; font-size: 12px; margin: 0 auto; max-width: 90%; }
            .input-container { display: flex; justify-content: center; margin-top: 20px; max-width: 90%; margin-left: auto; margin-right: auto; }
            input { flex-grow: 1; padding: 12px; background: #000; border: 1px solid #ff00ff; color: #fff; outline: none; }
            input:focus { box-shadow: 0 0 8px #00ffff; border-color: #00ffff; }
            button { padding: 12px; background: #ff00ff; color: #000; border: none; font-weight: bold; cursor: pointer; margin-left: 10px; }
            .signal { color: #00ff00; }
            @media (max-width: 600px) {
                body { padding: 10px; }
                .box { margin: 10px auto; padding: 15px; }
                #chat { height: 300px; margin: 0 auto; }
                .input-container { flex-direction: row; margin-top: 15px; }
                input { width: 70%; }
                button { margin-left: 5px; padding: 10px; }
            }
        </style>
    </head>
    <body>
        <h1>AGGRESSIVE SNIPER SWARM</h1>
        <div class="box">
            TOTAL SIGNALS CAPTURED: <span id="t">{{t}}</span> | NEXT BATCH: <span id="n">{{n}}</span><br>
            OPERATOR: {{op[:10]}}... | COLLECTOR: {{coll[:10]}}...
        </div>
        <div id="chat"></div><br>
        <div class="input-container">
            <input id="i" placeholder="/start-swarm...">
            <button onclick="s()">SEND</button>
        </div>
        <script>
            async function s(){
                const i=document.getElementById("i");
                if(!i.value) return;
                const sendButton = document.querySelector("button");
                sendButton.innerText = "TRANSMITTING...";
                sendButton.disabled = true;
                await fetch("/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:i.value})});
                i.value="";
                sendButton.innerText = "SEND";
                sendButton.disabled = false;
            }
            async function u(){
                const r=await fetch("/data"); 
                const d=await r.json(); 
                document.getElementById("t").innerText=d.t; 
                document.getElementById("n").innerText=d.n; 
                document.getElementById("chat").innerHTML=d.m.map(x=>`<div class="${x.includes(\'CRITICAL\')?\'signal\':\'\'}">`+x+"</div>").join("");
            }
            setInterval(u, 2000);
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
    return jsonify({"t":bridge_state["total_data_points"],"n":bridge_state["next_batch_countdown"],"m":bridge_state["swarm_responses"][:30]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
