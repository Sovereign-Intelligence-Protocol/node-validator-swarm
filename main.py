from flask import Flask, render_template_string, request, jsonify
import redis, os, threading, time, json, re, random, csv
from playwright.sync_api import sync_playwright

# --- Safety imports ---
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests, BeautifulSoup = None, None

app = Flask(__name__)

# --- Reality Bridge Configuration (Environment Variables) ---
OPERATOR_NODE_ID = os.getenv("OPERATOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")
COLLECTOR_NODE_ID = os.getenv("COLLECTOR_NODE_ID", "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

print(f"[*] INITIALIZING REALITY BRIDGE...")
print(f"[*] OPERATOR NODE: {OPERATOR_NODE_ID}")
print(f"[*] COLLECTOR NODE: {COLLECTOR_NODE_ID}")

try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("[+] REDIS NODE CONNECTED.")
except Exception as e:
    print(f"[-] REDIS NODE FAILED: {e}")
    r = None

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

def scrape_real_data_playwright(query, search_depth=3):
    data_points = []
    print(f"[*] OPERATOR NODE STARTING SEARCH: {query}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for i in range(search_depth):
                print(f"[*] VALIDATING DATA PAGE {i+1}...")
                page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=lcl&start={i * 20}")
                if page.locator("text=CAPTCHA").is_visible() or page.locator("text=unusual traffic").is_visible():
                    print("[-] SEARCH BLOCKED: CAPTCHA DETECTED.")
                    if r: r.lpush("swarm_responses", "🚨 CAPTCHA DETECTED! Manual node takeover required.")
                    browser.close()
                    return data_points
                soup = BeautifulSoup(page.content(), "html.parser")
                for res in soup.find_all("div", class_="VkpGBb"):
                    entity = res.find("div", class_="OSrXXb").text if res.find("div", class_="OSrXXb") else "N/A"
                    identifier = res.find("span", class_="LgQiCc").text if res.find("span", class_="LgQiCc") else "N/A"
                    data_points.append([entity, identifier])
            browser.close()
    except Exception as e:
        print(f"[-] NODE ERROR: {e}")
    print(f"[+] SEARCH COMPLETE. CAPTURED {len(data_points)} DATA POINTS.")
    return data_points

def swarm_engine():
    print("[*] SWARM ENGINE THREAD ACTIVE.")
    # --- HARD-CODED AUTO-START ---
    if r: 
        r.set("swarm_active", "true")
        r.lpush("swarm_responses", "🚀 REALITY BRIDGE AUTO-ACTIVATED.")
    
    city_idx, cat_idx = 0, 0
    while True:
        try:
            if not r: 
                time.sleep(5)
                continue
            
            if not r.exists("total_data_points"): r.set("total_data_points", 0)
            if not r.exists("next_batch_countdown"): r.set("next_batch_countdown", NODE_BATCH_SIZE)
            
            cmd = r.rpop("swarm_commands")
            if cmd:
                msg = str(cmd).strip()
                print(f"[*] COMMAND RECEIVED: {msg}")
                if msg.startswith("/start-swarm"):
                    r.set("swarm_active", "true")
                    r.lpush("swarm_responses", f"🚀 REALITY BRIDGE ACTIVE. Operator: {OPERATOR_NODE_ID[:8]}... Collector: {COLLECTOR_NODE_ID[:8]}...")
                    print("[+] SWARM ACTIVATED.")

            if r.get("swarm_active") == "true":
                city, cat = TOP_50_CITIES[city_idx], TARGET_CATEGORIES[cat_idx]
                verified_data = scrape_real_data_playwright(f"{cat} in {city}", search_depth=3)
                
                if verified_data:
                    count = len(verified_data)
                    r.incrby("total_data_points", count)
                    r.decrby("next_batch_countdown", count)
                    r.lpush("swarm_responses", f"✅ VALIDATED {count} DATA POINTS in {city} ({cat})")
                    if count > 0:
                        r.lpush("swarm_responses", f"📍 FIRST REAL LEAD: {verified_data[0][0]} | {verified_data[0][1]}")

                if int(r.get("next_batch_countdown")) <= 0:
                    r.set("next_batch_countdown", NODE_BATCH_SIZE)
                    r.lpush("swarm_responses", f"✅ BATCH FULL: DATA HANDOFF TO COLLECTOR: {COLLECTOR_NODE_ID[:8]}...")
                    print(f"[+] BATCH COMPLETE. HANDOFF TO {COLLECTOR_NODE_ID}")
                
                cat_idx = (cat_idx + 1) % len(TARGET_CATEGORIES)
                if cat_idx == 0: city_idx = (city_idx + 1) % len(TOP_50_CITIES)
            
            time.sleep(2)
        except Exception as e:
            print(f"[-] ENGINE ERROR: {e}")
            time.sleep(5)

threading.Thread(target=swarm_engine, daemon=True).start()

@app.route("/health")
def health():
    return "200 OK", 200

@app.route("/")
@app.route("/dashboard")
def index():
    t = r.get("total_data_points") if r else 0
    n = r.get("next_batch_countdown") if r else NODE_BATCH_SIZE
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
    """, t=t, n=n, op=OPERATOR_NODE_ID, coll=COLLECTOR_NODE_ID)

@app.route("/send", methods=["POST"])
def send():
    msg = request.json.get("message")
    if r: 
        r.lpush("swarm_commands", msg)
    return jsonify({"ok":True})

@app.route("/data")
def data():
    if not r: return jsonify({"t":0,"n":NODE_BATCH_SIZE,"m":[]})
    return jsonify({"t":r.get("total_data_points") or 0,"n":r.get("next_batch_countdown") or NODE_BATCH_SIZE,"m":r.lrange("swarm_responses",0,20)})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
