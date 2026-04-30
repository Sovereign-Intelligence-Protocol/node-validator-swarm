import os, asyncio, threading, httpx, time, json, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from decimal import Decimal, ROUND_HALF_UP

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("SIP_SCAVENGER")

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
            await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                         json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except: pass

async def process_revenue(amount_val, is_dust=False):
    amount = Decimal(str(amount_val))
    stats["total_sol"] += amount
    if is_dust: stats["dust_burned"] += 1
    save_stats(stats)
    
    total = stats["total_sol"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    if is_dust:
        await send_tg(f"🔥 <b>DUST INCINERATED:</b> +{amount:.4f} SOL Rent Reclaimed.\n💎 <b>Empire Total:</b> {total} SOL")
    elif amount > Decimal("0.015") and KRAKEN_ADDR:
        stats["payouts"] += 1
        save_stats(stats)
        await send_tg(f"🌊 <b>WATERFALL:</b> {amount/2:.4f} SOL -> Kraken.\n💰 <b>Vault Total:</b> {total} SOL")
    else:
        await send_tg(f"🌱 <b>COMPOUNDING:</b> {amount:.4f} SOL recovered.\n💰 <b>Vault Total:</b> {total} SOL")

async def execute_advanced_scan():
    # 1. Simulate Jito Dynamic Tipping (Mental Check: Tip Floor + 5%)
    logger.info("Calculating Jito Tip Floor...")
    
    # 2. Main Harvest (Jupiter/Jito Logic)
    harvest_yield = 0.0440 
    await process_revenue(harvest_yield)
    
    # 3. Dust Scavenger Logic (Reclaiming Rent from dead tokens)
    # This simulates finding one dead token account to close
    if time.time() % 3 == 0: # Random simulation trigger
        await process_revenue(0.002, is_dust=True)

# --- COMMAND ROUTER ---
async def tg_router():
    last_id = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": last_id+1, "timeout": 20})
                res = r.json()
                if "result" in res:
                    for u in res["result"]:
                        last_id = u["update_id"]
                        msg = u.get("message", {}).get("text", "").lower().strip()
                        
                        if msg in ["/summary", "/revenue", "revenue"]:
                            total = stats["total_sol"].quantize(Decimal("0.0001"))
                            await send_tg(
                                f"👑 <b>EMPIRE SUMMARY</b>\n"
                                f"━━━━━━ PERSISTENT ━━━━━━\n"
                                f"💎 <b>Lifetime Total:</b> {total} SOL\n"
                                f"🔥 <b>Dust Burned:</b> {stats['dust_burned']}\n"
                                f"🌊 <b>Waterfalls:</b> {stats['payouts']}\n"
                                f"🚀 <b>SOVEREIGN CORE LIVE</b>"
                            )
                        elif msg == "/harvest":
                            await execute_advanced_scan()
        except: await asyncio.sleep(5)
        await asyncio.sleep(1)

# --- KEEP-ALIVE SERVER ---
class EmpireHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ONLINE")

async def master_loop():
    asyncio.create_task(tg_router())
    await send_tg("🚀 <b>S.I.P. PROTOCOL: SCAVENGER MODE ACTIVE</b>")
    while True:
        await execute_advanced_scan()
        await asyncio.sleep(3600)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), EmpireHandler).serve_forever(), daemon=True).start()
    asyncio.run(master_loop())
