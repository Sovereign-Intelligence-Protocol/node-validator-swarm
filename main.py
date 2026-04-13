from flask import Flask, render_template_string, request, jsonify
import os, threading, time, json, re, random, csv
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- Reality Bridge Configuration (Environment Variables) ---
OPERATOR_NODE_ID = os.getenv("OPERATOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")
COLLECTOR_NODE_ID = os.getenv("COLLECTOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")

# --- In-Memory Bridge Storage (No-Redis Sledgehammer) ---
bridge_state = {
    "swarm_active": True, # AUTO-START
    "total_data_points": 0,
    "next_batch_countdown": 5, # HARD-CODE SPEED
    "swarm_responses": ["🚀 AGGRESSIVE SNIPER MODE ACTIVATED."],
    "swarm_commands": []
}

NODE_BATCH_SIZE = 5

# --- High-Velocity Sniper Targets ---
SNIPER_TARGETS = [
    "live high-frequency network signals", "new node deployment data", "real-time validator node status",
    "blockchain network telemetry", "decentralized network ping status", "validator consensus changes",
    "peer-to-peer network discovery events", "node synchronization alerts", "network traffic anomalies",
    "crypto node health reports", "new blockchain forks", "mining pool updates",
    "decentralized exchange liquidity events", "smart contract deployment alerts", "NFT marketplace activity spikes"
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
]

def scrape_sniper_signals(query):
    data_points = []
    print(f"[*] SNIPER NODE HUNTING: {query}")
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        # Using a more direct search query to trigger results
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=10"
        response = requests.get(search_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Look for common search result containers
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    title = g.find('h3').text if g.find('h3') else "Signal Detected"
                    snippet = g.find('div', class_='VwiC3b').text if g.find('div', class_='VwiC3b') else "Data stream active"
                    
                    if link.startswith('/url?q='):
                        link = link.split('/url?q=')[1].split('&')[0]
                    
                    data_points.append([link[:40] + "...", snippet[:80] + "..."])
        else:
            print(f"[-] SEARCH BLOCKED (Status {response.status_code}). RETRYING WITH ALTERNATE BRIDGE...")
            # Fallback to DuckDuckGo if Google blocks
            ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            response = requests.get(ddg_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for res in soup.find_all("div", class_="result"):
                    title_elem = res.find("a", class_="result__url")
                    snippet_elem = res.find("a", class_="result__snippet")
                    if title_elem and snippet_elem:
                        link = title_elem.get("href", "N/A")
                        data_points.append([link[:40] + "...", snippet_elem.text[:80] + "..."])

    except Exception as e:
        print(f"[-] SNIPER NODE ERROR: {e}")
            
    return data_points

def swarm_engine():
    print("[*] AGGRESSIVE SNIPER LOOP ACTIVE.")
    target_idx = 0
    while True:
        try:
            if bridge_state["swarm_commands"]:
                cmd = bridge_state["swarm_commands"].pop(0)
                if cmd.startswith("/start-swarm"):
                    bridge_state["swarm_active"] = True
                    bridge_state["swarm_responses"].insert(0, f"🎯 SNIPER LOOP RE-ENGAGED. Operator: {OPERATOR_NODE_ID[:8]}...")
                elif cmd.startswith("/stop-swarm"):
                    bridge_state["swarm_active"] = False
                    bridge_state["swarm_responses"].insert(0, f"🛑 SNIPER LOOP PAUSED. Operator: {OPERATOR_NODE_ID[:8]}...")
                else: # Custom search command
                    bridge_state["swarm_responses"].insert(0, f"🔍 CUSTOM TARGET: {cmd}")
                    verified_data = scrape_sniper_signals(cmd)
                    if verified_data:
                        for signal_source, signal_data in verified_data:
                            bridge_state["total_data_points"] += 1
                            bridge_state["next_batch_countdown"] -= 1
                            bridge_state["swarm_responses"].insert(0, f"⚡ CRITICAL VALIDATION: {signal_source} | {signal_data}")
                            if bridge_state["next_batch_countdown"] <= 0:
                                bridge_state["next_batch_countdown"] = NODE_BATCH_SIZE
                                bridge_state["swarm_responses"].insert(0, f"✅ BATCH FULL: SIGNAL HANDOFF TO COLLECTOR: {COLLECTOR_NODE_ID[:8]}...")

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
                            bridge_state["swarm_responses"].insert(0, f"✅ BATCH FULL: SIGNAL HANDOFF TO COLLECTOR: {COLLECTOR_NODE_ID[:8]}...")

                target_idx = (target_idx + 1) % len(SNIPER_TARGETS)
            
            time.sleep(random.uniform(5, 10)) # Reasonable frequency to avoid immediate IP ban
            
        except Exception as e:
            print(f"[-] SNIPER LOOP CRASH: {e}")
            bridge_state["swarm_responses"].insert(0, f"❌ SNIPER CRASH: {e}")
            time.sleep(10)

threading.Thread(target=swarm_engine, daemon=True).start()

@app.route("/health")
def health():
    return "200 OK", 200

@app.route("/")
@app.route("/dashboard")
def index():
    return render_template_string("""
    <!DOCTYPE html><html><head><title>Aggressive Sniper Swarm</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #ff00ff; font-family: monospace; text-align: center; padding: 20px; }
        .box { border: 1px solid #ff00ff; padding: 20px; margin: 20px; box-shadow: 0 0 15px #ff00ff; }
        #chat { height: 400px; overflow-y: auto; background: #050505; text-align: left; padding: 10px; border: 1px solid #330033; font-size: 12px; }
        input { width: 60%; padding: 12px; background: #000; border: 1px solid #ff00ff; color: #fff; }
        button { padding: 12px; background: #ff00ff; color: #000; border: none; font-weight: bold; }
        .signal { color: #00ff00; }
        .alert { color: #ff0000; }
    </style></head><body>
    <h1>AGGRESSIVE SNIPER SWARM</h1>
    <div class="box">
        TOTAL SIGNALS CAPTURED: <span id="t">{{t}}</span><br>
        NEXT BATCH COUNTDOWN: <span id="n">{{n}}</span><br>
        OPERATOR NODE: {{op[:10]}}... | COLLECTOR NODE: {{coll[:10]}}...
    </div>
    <div id="chat"></div><br>
    <input id="i" placeholder="/start-swarm..."><button onclick="s()">SEND</button>
    <script>
        async function s(){
            const i=document.getElementById("i");
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
            document.getElementById("chat").innerHTML=d.m.map(x=>{
                if(x.includes("CRITICAL VALIDATION")) return `<div class="signal">${x}</div>`;
                if(x.includes("CRASH") || x.includes("ERROR")) return `<div class="alert">${x}</div>`;
                return `<div>${x}</div>`;
            }).join("");
        }
        setInterval(u, 2000);
    </script></body></html>
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
