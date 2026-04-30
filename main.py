import os, asyncio, threading, httpx, time, json, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from decimal import Decimal, ROUND_HALF_UP

# --- LOGGING SETUP ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("SIP_CORE")

# --- CONFIG ---
PORT = int(os.environ.get("PORT", 10000))
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
KRAKEN_ADDR = os.environ.get("KRAKEN_DEPOSIT_ADDRESS")
DISK_PATH = "/data/revenue.json"

# Global lock to prevent overlapping scans
scan_lock = asyncio.Lock()

# --- DISK PERSISTENCE ---
def load_stats():
    if not os.path.exists("/data"):
        try: os.makedirs("/data")
        except Exception as e: logger.error(f"Failed to create /data: {e}")
        
    if os.path.exists(DISK_PATH):
        try:
            with open(DISK_PATH, 'r') as f:
                data = json.load(f)
                # Convert back to Decimal for math safety
                data["total_sol"] = Decimal(str(data.get("total_sol", "0.0")))
                return data
        except Exception as e: 
            logger.error(f"Disk read error: {e}")
    
    return {"total_sol": Decimal("0.0"), "payouts": 0, "start_time": time.time()}

def save_stats(data):
    try:
        # Convert Decimal to string/float for JSON serialization
        temp_data = data.copy()
        temp_data["total_sol"] = float(data["total_sol"])
        with open(DISK_PATH, 'w') as f:
            json.dump(temp_data, f)
    except Exception as e: 
        logger.error(f"Disk write error: {e}")

stats = load_stats()

# --- THE ENGINE ---
async def send_tg(msg):
    async with httpx.AsyncClient() as c:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            payload = {"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"}
            await c.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Telegram notify failed: {e}")

async def distribute_harvest(amount_val):
    amount = Decimal(str(amount_val))
    stats["total_sol"] += amount
    save_stats(stats)
    
    total_display = stats["total_sol"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    if amount > Decimal("0.015") and KRAKEN_ADDR:
        stats["payouts"] += 1
        save_stats(stats)
        await send_tg(f"🌊 <b>WATERFALL:</b> {amount/2:.4f} SOL -> Kraken.\n💰 <b>Total:</b> {total_display} SOL")
    else:
        await send_tg(f"🌱 <b>COMPOUNDING:</b> {amount:.4f} SOL recovered.\n💎 <b>Lifetime:</b> {total_display} SOL")

async def execute_parabolic_scan():
    if scan_lock.locked():
        logger.warning("Scan already in progress. Skipping...")
        return

    async with scan_lock:
        try:
            logger.info("Executing Parabolic Scan...")
            # Logic integration: Replace 0.0440 with your actual Jito/Jupiter yield variable
            current_yield = 0.0440 
            await distribute_harvest(current_yield)
        except Exception as e:
            logger.error(f"Scan failed: {e}")

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
                        
                        if msg in ["/summary", "/revenue", "revenue"]:
                            uptime_hrs = (time.time() - stats["start_time"]) / 3600
                            total = stats["total_sol"].quantize(Decimal("0.0001"))
                            await send_tg(
                                f"👑 <b>EMPIRE SUMMARY</b>\n"
                                f"━━━━━━ PERSISTENT ━━━━━━\n"
                                f"💎 <b>Lifetime Total:</b> {total} SOL\n"
                                f"🌊 <b>Waterfalls:</b> {stats['payouts']}\n"
                                f"⏱️ <b>Uptime:</b> {uptime_hrs:.1f} Hours\n"
                                f"🚀 <b>SOVEREIGN CORE LIVE</b>"
                            )
                        elif msg == "/harvest":
                            asyncio.create_task(execute_parabolic_scan())
        except Exception as e:
            logger.error(f"Router error: {e}")
            await asyncio.sleep(5) # Backoff on error
        await asyncio.sleep(1)

# --- KEEP-ALIVE SERVER ---
class EmpireHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ONLINE")

async def master_loop():
    asyncio.create_task(tg_router())
    await send_tg("🚀 <b>SOVEREIGN PERSISTENT CORE LIVE</b>")
    while True:
        await execute_parabolic_scan()
        await asyncio.sleep(3600) # One scan per hour

if __name__ == "__main__":
    # Start Keep-Alive Server
    server = HTTPServer(('0.0.0.0', PORT), EmpireHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    
    # Run Async Engine
    try:
        asyncio.run(master_loop())
    except KeyboardInterrupt:
        logger.info("Sovereign Core shutting down.")
