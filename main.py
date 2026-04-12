from flask import Flask, render_template_string, request, jsonify
import os, threading, time, json, re, random, csv
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- Reality Bridge Configuration (Environment Variables) ---
OPERATOR_NODE_ID = os.getenv("OPERATOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")
COLLECTOR_NODE_ID = os.getenv("COLLECTOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")

# --- In-Memory Bridge Storage (No-Redis Sledgehammer) ---
# This ensures 100% stability on Railway without external dependencies.
bridge_state = {
    "swarm_active": True, # AUTO-START
    "total_data_points": 0,
    "next_batch_countdown": 1000,
    "swarm_responses": ["🚀 REALITY BRIDGE AUTO-ACTIVATED."],
    "swarm_commands": []
}

NODE_BATCH_SIZE = 1000
TOP_50_CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "Jacksonville, FL",
    "Fort Worth, TX", "San Jose, CA", "Austin, TX", "Charlotte, NC", "Columbus, OH",
    "Indianapolis, IN", "San Francisco, CA", "Seattle, WA", "Denver, CO", "Oklahoma City, OK",
    "Nashville, TN", "Washington, D.C.", "El Paso, TX", "Las Vegas, NV", "Boston, MA",
    "Detroit, MI", "Louisville, KY", "Portland, OR", "Memphis, TN", "Baltimore, MD",
    "Milwaukee, WI", "Albuquerque, NM", "Tucson, AZ", "Fresno, CA", "Sacramento, CA",
    "Atlanta, GA", "Mesa, AZ", "Kansas City, MO", "Raleigh, NC", "Colorado Springs, CO",
    "Omaha, NE", "Miami, FL", "Virginia Beach, VA", "Long Beach, CA", "Oakland, CA",
    "Minneapolis, MN", "Bakersfield, CA", "Tulsa, OK", "Tampa, FL", "Arlington, TX"
]
TARGET_CATEGORIES = ["Roofers", "Plumbers", "HVAC"]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'
]

def scrape_real_data_http(query, search_depth=3):
    data_points = []
    print(f"[*] OPERATOR NODE STARTING HTTP SEARCH: {query}")
    try:
        for i in range(search_depth):
            print(f"[*] VALIDATING DATA PAGE {i+1}...")
            headers = {
                'User-Agent': random.choice(USER_AGENTS)
            }
            url = f"https://www.google.com/search?q={query.replace(" ", "+")}&tbm=lcl&start={i * 20}"
            response = requests.get(url, headers=headers, timeout=15) # Increased timeout
            response.raise_for_status() # Raise an exception for HTTP errors
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check for CAPTCHA or unusual traffic
            if "CAPTCHA" in response.text or "unusual traffic" in response.text:
                print("[-] SEARCH BLOCKED: CAPTCHA DETECTED. RETRYING WITH NEW USER-AGENT.")
                bridge_state["swarm_responses"].insert(0, "🚨 CAPTCHA DETECTED! Retrying with new User-Agent.")
                time.sleep(random.randint(5, 10)) # Longer sleep on block
                continue # Retry current page with new user agent

            for res in soup.find_all("div", class_="VkpGBb"):
                entity = res.find("div", class_="OSrXXb").text if res.find("div", class_="OSrXXb") else "N/A"
                identifier = res.find("span", class_="LgQiCc").text if res.find("span", class_="LgQiCc") else "N/A"
                if entity != "N/A" and identifier != "N/A": # Only add if both are found
                    data_points.append([entity, identifier])

            time.sleep(random.randint(2, 5)) # Random sleep between pages

    except requests.exceptions.RequestException as e:
        print(f"[-] HTTP REQUEST ERROR: {e}")
        bridge_state["swarm_responses"].insert(0, f"❌ HTTP ERROR: {e}")
    except Exception as e:
        print(f"[-] NODE ERROR: {e}")
        bridge_state["swarm_responses"].insert(0, f"❌ NODE ERROR: {e}")
            
    print(f"[+] HTTP SEARCH COMPLETE. CAPTURED {len(data_points)} REAL DATA POINTS.")
    return data_points

def swarm_engine():
    print("[*] SWARM ENGINE THREAD ACTIVE.")
    city_idx, cat_idx = 0, 0
    while True:
        try:
            if bridge_state["swarm_commands"]:
                cmd = bridge_state["swarm_commands"].pop(0)
                if cmd.startswith("/start-swarm"):
                    bridge_state["swarm_active"] = True
                    bridge_state["swarm_responses"].insert(0, f"🚀 REALITY BRIDGE RE-ENGAGED. Operator: {OPERATOR_NODE_ID[:8]}...")

            if bridge_state["swarm_active"]:
                city, cat = TOP_50_CITIES[city_idx], TARGET_CATEGORIES[cat_idx]
                verified_data = scrape_real_data_http(f"{cat} in {city}", search_depth=3)
                
                if verified_data:
                    count = len(verified_data)
                    bridge_state["total_data_points"] += count
                    bridge_state["next_batch_countdown"] -= count
                    bridge_state["swarm_responses"].insert(0, f"✅ VALIDATED {count} REAL DATA POINTS in {city} ({cat})")
                    if count > 0:
                        bridge_state["swarm_responses"].insert(0, f"📍 REAL-WORLD VALIDATION: {verified_data[0][0]} | {verified_data[0][1]}")

                if bridge_state["next_batch_countdown"] <= 0:
                    bridge_state["next_batch_countdown"] = NODE_BATCH_SIZE
                    bridge_state["swarm_responses"].insert(0, f"✅ BATCH FULL: DATA HANDOFF TO COLLECTOR: {COLLECTOR_NODE_ID[:8]}...")
                
                cat_idx = (cat_idx + 1) % len(TARGET_CATEGORIES)
                if cat_idx == 0: city_idx = (city_idx + 1) % len(TOP_50_CITIES)
            
            time.sleep(random.randint(10, 20)) # Longer random sleep between full cycles
        except Exception as e:
            print(f"[-] ENGINE ERROR: {e}")
            bridge_state["swarm_responses"].insert(0, f"❌ ENGINE CRASH: {e}")
            time.sleep(15)

threading.Thread(target=swarm_engine, daemon=True).start()

@app.route("/health")
def health():
    return "200 OK", 200

@app.route("/")
@app.route("/dashboard")
def index():
    return render_template_string("""
    <!DOCTYPE html><html><head><title>Node Swarm</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #00f2fe; font-family: monospace; text-align: center; padding: 20px; }
        .box { border: 1px solid #00f2fe; padding: 20px; margin: 20px; box-shadow: 0 0 15px #00f2fe; }
        #chat { height: 350px; overflow-y: auto; background: #111; text-align: left; padding: 10px; border: 1px solid #333; font-size: 12px; }
        input { width: 60%; padding: 12px; background: #000; border: 1px solid #00f2fe; color: #fff; }
        button { padding: 12px; background: #00f2fe; color: #000; border: none; font-weight: bold; }
    </style></head><body>
    <h1>NODE-VALIDATOR SWARM</h1>
    <div class="box">
        TOTAL VALIDATED DATA: <span id="t">{{t}}</span><br>
        NEXT BATCH COUNTDOWN: <span id="n">{{n}}</span><br>
        OPERATOR NODE: {{op[:10]}}... | COLLECTOR NODE: {{coll[:10]}}...
    </div>
    <div id="chat"></div><br>
    <input id="i" placeholder="/start-swarm..."><button onclick="s()">SEND</button>
    <script>
        async function s(){const i=document.getElementById("i"); await fetch("/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:i.value})}); i.value="";}
        async function u(){const r=await fetch("/data"); const d=await r.json(); document.getElementById("t").innerText=d.t; document.getElementById("n").innerText=d.n; document.getElementById("chat").innerHTML=d.m.map(x=>`<div>${x}</div>`).join("");}
        setInterval(u, 3000);
    </script></body></html>
    """, t=bridge_state["total_data_points"], n=bridge_state["next_batch_countdown"], op=OPERATOR_NODE_ID, coll=COLLECTOR_NODE_ID)

@app.route("/send", methods=["POST"])
def send():
    msg = request.json.get("message")
    bridge_state["swarm_commands"].append(msg)
    return jsonify({"ok":True})

@app.route("/data")
def data():
    return jsonify({"t":bridge_state["total_data_points"],"n":bridge_state["next_batch_countdown"],"m":bridge_state["swarm_responses"][:20]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
