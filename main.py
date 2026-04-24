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
# This handles both Helius Payments AND Telegram Commands
@app.route('/helius-webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    
    # Check if the data is a Telegram Command
    if "message" in data:
        bot.process_new_updates([telebot.types.Update.de_json(data)])
        return "ok", 200

    # Otherwise, process as a Helius Payment
    for tx in data:
        if tx.get('type') == 'TRANSFER':
            for tr in tx.get('nativeTransfers', []):
                if tr['toUserAccount'] == CONFIG["HOT_WALLET"]:
                    uid = tx.get('instructions', [{}])[0].get('parsed', {}).get('info', {}).get('memo')
                    amt = tr['amount'] / 10**9
                    if uid and uid.isdigit():
                        tier = "WHALE" if amt >= CONFIG["TOLL_WHALE"] else "BASIC"
                        r.set(f"access:{uid}", tier, ex=2592000)
                        Ledger.log_event(uid, "PAYMENT", {"amt": amt, "tier": tier})
                        bot.send_message(uid, f"✅ **{tier} ACCESS GRANTED**")
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
    bot.reply_to(message, "🛡️ **SYSTEM ONLINE**\nWebhook Mode: Active\nTracking: Enabled")

@bot.message_handler(commands=['scrape'])
def hunter(message):
    uid = str(message.from_user.id)
    if uid != CONFIG["ADMIN"] and not r.get(f"access:{uid}"):
        return bot.reply_to(message, "🚫 **ACCESS DENIED**\nPay the 0.1 SOL toll to unlock.")
    bot.reply_to(message, "📡 **SCANNING MAINNET...**")

# --- 4. THE FINAL HANDSHAKE (NO POLLING) ---
if __name__ == "__main__":
    # Tell Telegram to send all commands to your Render URL
    # This replaces infinity_polling() completely
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/helius-webhook"
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    
    # Start the Flask Server
    app.run(host='0.0.0.0', port=10000)
