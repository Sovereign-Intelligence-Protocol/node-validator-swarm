import os, time, redis, telebot, threading, requests
from flask import Flask, request, jsonify
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# --- CORE SETTINGS ---
CONFIG = {
    "TOLL_BASIC": 0.1,
    "TOLL_WHALE": 0.5,
    "SWEEP_THRESHOLD": 1.5,
    "ADMIN": os.getenv("ADMIN_ID"),
    "HOT_WALLET": os.getenv("SOLANA_WALLET_ADDRESS")
}

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
app = Flask(__name__)

# --- 1. TELEMETRY ENGINE ---
class Ledger:
    @staticmethod
    def log_event(uid, event, meta=None):
        entry = {"uid": str(uid), "event": event, "ts": time.time(), "meta": str(meta)}
        r.xadd("protocol_logs", entry, maxlen=10000)
        r.hset(f"u:{uid}", "last_act", time.time())
        if event == "PAYMENT":
            r.incrbyfloat("total_rev", meta.get("amt", 0))

# --- 2. THE DUAL-PURPOSE WEBHOOK ---
@app.route('/helius-webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    
    # Logic for Telegram Commands
    if isinstance(data, dict) and "update_id" in data:
        bot.process_new_updates([telebot.types.Update.de_json(data)])
        return "ok", 200

    # Logic for Helius Payments
    if isinstance(data, list):
        for tx in data:
            if tx.get('type') == 'TRANSFER':
                for tr in tx.get('nativeTransfers', []):
                    if tr['toUserAccount'] == CONFIG["HOT_WALLET"]:
                        # Pull memo from instructions
                        memo_raw = tx.get('instructions', [{}])[0].get('parsed', {}).get('info', {}).get('memo', "")
                        if memo_raw.isdigit():
                            amt = tr['amount'] / 10**9
                            tier = "WHALE" if amt >= CONFIG["TOLL_WHALE"] else "BASIC"
                            r.set(f"access:{memo_raw}", tier, ex=2592000)
                            Ledger.log_event(memo_raw, "PAYMENT", {"amt": amt, "tier": tier})
                            bot.send_message(memo_raw, f"✅ **{tier} ACCESS GRANTED**")
    return jsonify({"status": "ok"}), 200

# --- 3. COMMAND HANDLERS ---
@bot.message_handler(commands=['stats'])
def show_god_view(message):
    if str(message.from_user.id) != CONFIG["ADMIN"]: return
    rev = r.get("total_rev") or 0
    subs = len(r.keys("access:*"))
    logs = r.xrevrange("protocol_logs", count=5)
    msg = (f"👑 **OMNI-SOVEREIGN DASHBOARD**\n💰 Lifetime Rev: `{rev} SOL`\n👥 Active Subs: `{subs}`\n\n📡 **Live Feed:**\n")
    for _, l in logs: msg += f"• {l['uid']} | {l['event']}\n"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['health'])
def health_check(message):
    bot.reply_to(message, "🛡️ **SYSTEM ONLINE**\nMode: Webhook v12.2\nTracking: Enabled")

@bot.message_handler(commands=['scrape'])
def hunter(message):
    uid = str(message.from_user.id)
    if uid != CONFIG["ADMIN"] and not r.get(f"access:{uid}"):
        return bot.reply_to(message, "🚫 **ACCESS DENIED**\nPay toll to unlock.")
    bot.reply_to(message, "📡 **SCANNING MAINNET...**")

# --- 4. STARTUP (HARD-CODED WEBHOOK) ---
if __name__ == "__main__":
    # Hard-coded your specific Render address to fix the "Bad Webhook" error
    FINAL_URL = "https://lead-scalper-bot-5to8.onrender.com/helius-webhook"
    
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url=FINAL_URL)
    
    print(f"S.I.P. v12.2 Online at {FINAL_URL}")
    app.run(host='0.0.0.0', port=10000)
