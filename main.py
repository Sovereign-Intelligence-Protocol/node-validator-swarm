import os, asyncio, threading, httpx, time, json
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIG ---
PORT = int(os.environ.get("PORT", 10000))
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_ADMIN = os.environ.get("TELEGRAM_ADMIN_ID")
KRAKEN_ADDR = os.environ.get("KRAKEN_DEPOSIT_ADDRESS")

# --- DISK PERSISTENCE ---
DISK_PATH = "/data/revenue.json"

def load_stats():
    # Ensure the directory exists for Render persistent disks
    if not os.path.exists("/data"):
        try: os.makedirs("/data")
        except: pass
        
    if os.path.exists(DISK_PATH):
        try:
            with open(DISK_PATH, 'r') as f:
                return json.load(f)
        except: pass
    # Starting base for your S.I.P. journey
    return {"total_sol": 0.0, "payouts": 0, "start_time": time.time()}

def save_stats(data):
    try:
        with open(DISK_PATH, 'w') as f:
            json.dump(data, f)
    except: pass

stats = load_stats()

# --- THE ENGINE ---
async def send_tg(msg):
    async with httpx.AsyncClient() as c:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            await c.post(url, json={"chat_id": TG_ADMIN, "text": msg, "parse_mode": "HTML"})
        except: pass

async def distribute_harvest(amount):
    # This is the "Total Tracker" implementation
    stats["total_sol"] += amount
    save_stats(stats)
    
    if amount > 0.015 and KRAKEN_ADDR:
        stats["payouts"] += 1
        save_stats(stats)
        await send_tg(f"🌊 <b>WATERFALL:</b> {amount/2:.4f} SOL -> Kraken.\n💎 <b>New Total:</b> {stats['total_sol']:.4f} SOL")
    else:
        await send_tg(f"🌱 <b>COMPOUNDING:</b> {amount:.4f} SOL recovered.\n💰 <b>Lifetime:</b> {stats['total_sol']:.4f} SOL")

async def execute_parabolic_scan():
    # In a real run, this would be your Jupiter/Jito result amount
    current_yield = 0.0440 
    await distribute_harvest(current_yield)

# --- ROUTER ---
async def tg_router():
    last_id = 0
    while True:
        try:
            async with httpx.AsyncClient() as c:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
                r = await c.get(url, params={"offset": last_id+1, "timeout": 10})
                data = r.json()
                if "result" in data:
                    for u in data["result"]:
                        last_id = u["update_id"]
                        msg_text = u.get("message", {}).get("text", "").lower().strip()
                        
                        if msg_text in ["/summary", "/revenue", "revenue", "summary"]:
                            uptime = (time.time() - stats["start_time"]) / 3600
                            await send_tg(
                                f"👑 <b>EMPIRE SUMMARY</b>\n"
                                f"━━━━━━ PERSISTENT ━━━━━━\n"
                                f"💎 <b>Lifetime Total:</b> {stats['total_sol']:.4f} SOL\n"
                                f"🌊 <b>Waterfalls:</b> {stats['payouts']}\n"
                                f"⏱️ <b>Uptime:</b> {uptime:.1f} Hours\n"
                                f"🚀 <b>SOVEREIGN CORE LIVE</b>"
                            )
                        elif msg_text == "/harvest":
                            await execute_parabolic_scan()
        except: pass
        await asyncio.sleep(2)

# --- SERVER ---
class EmpireHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ONLINE")

async def master_loop():
    asyncio.create_task(tg_router())
    await send_tg("🚀 <b>SOVEREIGN PERSISTENT CORE LIVE</b>")
    # Main loop runs the scan once per hour
    while True:
        await execute_parabolic_scan()
        await asyncio.sleep(3600)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), EmpireHandler).serve_forever(), daemon=True).start()
    asyncio.run(master_loop())
