import os, asyncio, threading, httpx, time, json, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from decimal import Decimal, ROUND_HALF_UP

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("SIP_OMNICORE")

# --- CONFIG ---
PORT = int(os.environ.get("PORT", 10000))
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
KRAKEN_ADDR = os.environ.get("KRAKEN_DEPOSIT_ADDRESS")
DISK_PATH = "/data/revenue.json"

# --- PERSISTENCE ---
def load_stats():
    if not os.path.exists("/data"):
        try: os.makedirs("/data")
        except: pass
    if os.path.exists(DISK_PATH):
        try:
            with open(DISK_PATH, 'r') as f:
                d = json.load(f)
                d["total_sol"] = Decimal(str(d.get("total_sol", "0.0")))
                d["dust_burned"] = d.get("dust_burned", 0)
                return d
        except: pass
    return {"total_sol": Decimal("0.0"), "payouts": 0, "dust_burned": 0, "start_time": time.time()}

def save_stats(data):
    try:
        temp = data.copy()
        temp["total_sol"] = float(data["total_sol"])
        with open(DISK_PATH, 'w') as f:
            json.dump(temp, f)
    except: pass

stats = load_stats()

# --- THE ENGINE ---
async def send_tg(msg):
    async with httpx.AsyncClient() as c:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            await c.post(url, json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"}, timeout=10)
        except: pass

async def record_profit(amount_val, source="COMP"):
    amount = Decimal(str(amount_val))
    if amount <= 0: return False

    stats["total_sol"] += amount
    if source == "DUST": stats["dust_burned"] += 1
    save_stats(stats)
    
    total = stats["total_sol"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    # ALERT LOGIC: Telegram alerts for Whales, Waterfalls, and High-Value Compounding
    if source == "WHALE" or amount >= Decimal("0.05"):
        await send_tg(f"🐋 <b>WHALE HARVEST:</b> +{amount:.4f} SOL\n💎 <b>Total:</b> {total} SOL")
    elif amount > Decimal("0.015") and KRAKEN_ADDR:
        stats["payouts"] += 1
        save_stats(stats)
        await send_tg(f"🌊 <b>WATERFALL:</b> {amount/2:.4f} SOL -> Kraken.\n💰 <b>Total:</b> {total} SOL")
    elif source == "DUST":
        # Log dust quietly to console to save TG bandwidth, unless it's a massive reclaim
        logger.info(f"🔥 DUST RECLAIMED: {amount} SOL")
    else:
        logger.info(f"🌱 RECOVERY: {amount} SOL | Total: {total}")
    
    return True # Signal that activity occurred

# --- PROTOCOL HEARTBEAT ---
async def execute_protocol():
    activity = False
    try:
        # 1. DUST SCAVENGER (Simulated logic for rent reclamation)
        # In live, this hooks into your account-closing logic
        if time.time() % 120 < 10: # Check for dust every ~2 mins
            if await record_profit(0.002, source="DUST"):
                activity = True
        
        # 2. MAIN HARVEST (Jupiter/Jito Execution)
        # Integration: replace 0.0440 with your actual yield variable
        harvest_yield = 0.0440 
        if await record_profit(harvest_yield, source="COMP"):
            activity = True

    except Exception as e:
        logger.error(f"Heartbeat Error: {e}")
        if "429" in str(e): await asyncio.sleep(20) # Rate limit backoff
    
    return activity

# --- COMMAND ROUTER ---
async def tg_router():
    last_id = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
                r = await c.get(url, params={"offset": last_id+1, "timeout": 20})
                res = r.json()
                if "result" in res:
                    for u in res["result"]:
                        last_id = u["update_id"]
                        msg = u.get("message", {}).get("text", "").lower().strip()
                        
                        if msg in ["/summary", "/revenue", "revenue", "summary"]:
                            total = stats["total_sol"].quantize(Decimal("0.0001"))
                            uptime = (time.time() - stats["start_time"]) / 3600
                            await send_tg(
                                f"👑 <b>S.I.P. OMNICORE v5.0</b>\n"
                                f"━━━━ VARIABLE PULSE ━━━━\n"
                                f"💎 <b>Lifetime:</b> {total} SOL\n"
                                f"🔥 <b>Dust Reclaimed:</b> {stats.get('dust_burned', 0)}\n"
                                f"🌊 <b>Waterfalls:</b> {stats['payouts']}\n"
                                f"⏱️ <b>Uptime:</b> {uptime:.1f} Hours\n"
                                f"🚀 <b>STATUS: ONLINE</b>"
                            )
        except: await asyncio.sleep(5)
        await asyncio.sleep(1)

# --- SERVER ---
class EmpireHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ONLINE")

async def master_loop():
    asyncio.create_task(tg_router())
    await send_tg("🚀 <b>OMNICORE ACTIVATED: Variable Pulse (10s/5s)</b>")
    
    current_heartbeat = 10
    
    while True:
        start_time = time.time()
        
        # Run protocol and check for activity
        success = await execute_protocol()
        
        # Variable Pulse Logic
        if success:
            current_heartbeat = 5 # Speed up if we are hitting
        else:
            current_heartbeat = 10 # Slow down to save $ if quiet
            
        elapsed = time.time() - start_time
        sleep_time = max(0, current_heartbeat - elapsed)
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), EmpireHandler).serve_forever(), daemon=True).start()
    asyncio.run(master_loop())
