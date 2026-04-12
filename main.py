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
    "next_batch_countdown": 1000,
    "swarm_responses": ["🚀 HIGH-VELOCITY SNIPER MODE AUTO-ACTIVATED."],
    "swarm_commands": []
}

NODE_BATCH_SIZE = 1000

# --- High-Velocity Sniper Targets ---
SNIPER_TARGETS = [
    "live network signal", "new node deployment", "validator node status",
    "blockchain node active", "network telemetry data", "node synchronization status",
    "decentralized network ping", "validator consensus signal", "node latency report",
    "peer-to-peer network discovery"
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'
]

def scrape_sniper_signals(query, search_depth=3):
    data_points = []
    print(f"[*] SNIPER NODE HUNTING: {query}")
    try:
        for i in range(search_depth):
            headers = {
                'User-Agent': random.choice(USER_AGENTS)
            }
            # Using DuckDuckGo for faster, less restricted signal scraping
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}&s={i * 30}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for res in soup.find_all("div", class_="result"):
                title_elem = res.find("a", class_="result__url")
                snippet_elem = res.find("a", class_="result__snippet")
                
                if title_elem and snippet_elem:
                    signal_source = title_elem.get('href', 'N/A')
                    signal_data = snippet_elem.text.strip()
                    
                    # Filter for actual signal-like data (contains numbers, IPs, or specific keywords)
                    if any(char.isdigit() for char in signal_data) or "node" in signal_data.lower() or "network" in signal_data.lower():
                        # Clean up the source URL
                        if signal_source.startswith('//duckduckgo.com/l/?uddg='):
                            signal_source = signal_source.split('uddg=')[1].split('&')[0]
                            import urllib.parse
                            signal_source = urllib.parse.unquote(signal_source)
                            
                        data_points.append([signal_source[:50] + "...", signal_data[:100] + "..."])

            # Maximum Frequency: Minimal sleep between pages
            time.sleep(random.uniform(0.5, 1.5))

    except requests.exceptions.RequestException as e:
        print(f"[-] SNIPER HTTP ERROR: {e}")
    except Exception as e:
        print(f"[-] SNIPER NODE ERROR: {e}")
            
    print(f"[+] SNIPER HUNT COMPLETE. CAPTURED {len(data_points)} LIVE SIGNALS.")
    return data_points

def swarm_engine():
    print("[*] HIGH-VELOCITY SNIPER LOOP ACTIVE.")
    target_idx = 0
    while True:
        try:
            if bridge_state["swarm_commands"]:
                cmd = bridge_state["swarm_commands"].pop(0)
                if cmd.startswith("/start-swarm"):
                    bridge_state["swarm_active"] = True
                    bridge_state["swarm_responses"].insert(0, f"🎯 SNIPER LOOP RE-ENGAGED. Operator: {OPERATOR_NODE_ID[:8]}...")

            if bridge_state["swarm_active"]:
                target = SNIPER_TARGETS[target_idx]
                # Add a random timestamp or identifier to ensure fresh results
                dynamic_query = f'"{target}" "{time.strftime("%Y-%m-%d")}"'
                
                verified_data = scrape_sniper_signals(dynamic_query, search_depth=3)
                
                if verified_data:
                    count = len(verified_data)
                    bridge_state["total_data_points"] += count
                    bridge_state["next_batch_countdown"] -= count
                    bridge_state["swarm_responses"].insert(0, f"⚡ CAPTURED {count} LIVE SIGNALS: [{target.upper()}]")
                    
                    if count > 0:
                        # Report the first live signal found in this batch
                        bridge_state["swarm_responses"].insert(0, f"📡 LIVE SIGNAL: {verified_data[0][0]} | {verified_data[0][1]}")

                if bridge_state["next_batch_countdown"] <= 0:
                    bridge_state["next_batch_countdown"] = NODE_BATCH_SIZE
                    bridge_state["swarm_responses"].insert(0, f"✅ BATCH FULL: SIGNAL HANDOFF TO COLLECTOR: {COLLECTOR_NODE_ID[:8]}...")
                
                target_idx = (target_idx + 1) % len(SNIPER_TARGETS)
            
            # Maximum Frequency: Minimal sleep between full target cycles
            time.sleep(random.uniform(2.0, 4.0))
            
        except Exception as e:
            print(f"[-] SNIPER LOOP CRASH: {e}")
            bridge_state["swarm_responses"].insert(0, f"❌ SNIPER CRASH: {e}")
            time.sleep(5)

threading.Thread(target=swarm_engine, daemon=True).start()

@app.route("/health")
def health():
    return "200 OK", 200

@app.route("/")
@app.route("/dashboard")
def index():
    return render_template_string("""
    <!DOCTYPE html><html><head><title>Sniper Swarm</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #00ff00; font-family: monospace; text-align: center; padding: 20px; }
        .box { border: 1px solid #00ff00; padding: 20px; margin: 20px; box-shadow: 0 0 15px #00ff00; }
        #chat { height: 400px; overflow-y: auto; background: #050505; text-align: left; padding: 10px; border: 1px solid #003300; font-size: 12px; }
        input { width: 60%; padding: 12px; background: #000; border: 1px solid #00ff00; color: #fff; }
        button { padding: 12px; background: #00ff00; color: #000; border: none; font-weight: bold; }
        .signal { color: #ff00ff; }
        .alert { color: #ff0000; }
    </style></head><body>
    <h1>HIGH-VELOCITY SNIPER SWARM</h1>
    <div class="box">
        TOTAL SIGNALS CAPTURED: <span id="t">{{t}}</span><br>
        NEXT BATCH COUNTDOWN: <span id="n">{{n}}</span><br>
        OPERATOR NODE: {{op[:10]}}... | COLLECTOR NODE: {{coll[:10]}}...
    </div>
    <div id="chat"></div><br>
    <input id="i" placeholder="/start-swarm..."><button onclick="s()">SEND</button>
    <script>
        async function s(){const i=document.getElementById("i"); await fetch("/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:i.value})}); i.value="";}
        async function u(){
            const r=await fetch("/data"); 
            const d=await r.json(); 
            document.getElementById("t").innerText=d.t; 
            document.getElementById("n").innerText=d.n; 
            document.getElementById("chat").innerHTML=d.m.map(x=>{
                if(x.includes("LIVE SIGNAL")) return `<div class="signal">${x}</div>`;
                if(x.includes("CRASH") || x.includes("ERROR")) return `<div class="alert">${x}</div>`;
                return `<div>${x}</div>`;
            }).join("");
        }
        setInterval(u, 2000); // Faster UI updates for Sniper Mode
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
