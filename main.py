import os, time, redis, telebot, requests
from flask import Flask, request, jsonify

# --- 1. CORE SETTINGS ---
# Using os.getenv so you don't leak secrets in your code
CONFIG = {
    "TOLL_BASIC": 0.1,
    "TOLL_WHALE": 0.5,
    "ADMIN": os.getenv("ADMIN_ID"),
    "HOT_WALLET": os.getenv("SOLANA_WALLET_ADDRESS"),
    "KRAKEN_SETTLEMENT": os.getenv("KRAKEN_ADDRESS")
}

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
app = Flask(__name__)

# --- 2. THE REVENUE LEDGER ---
class Ledger:
    @staticmethod
    def log_event(uid, event, meta=None):
        # Database revenue bridging via Atomic Interoperability
        entry = {"uid": str(uid), "event": event, "ts": time.time(), "meta": str(meta)}
        r.xadd("protocol_logs", entry, maxlen=10000)
        r.hset(f"u:{uid}", "last_act", time.time())
        if event == "PAYMENT":
            r.incrbyfloat("total_rev", meta.get("amt", 0))

# --- 3. THE DUAL-PURPOSE TOLL BRIDGE (Webhooks) ---
@app.route('/helius-webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    
    # Handle Telegram Commands via Webhook
    if isinstance(data, dict) and "update_id" in data:
        bot.process_new_updates([telebot.types.Update.de_json(data)])
        return "ok", 200

    # Handle Helius Payment Signals (Solana Mainnet)
    if isinstance(data, list):
        for tx in data:
            if tx.get('type') == 'TRANSFER':
                for tr in tx.get('nativeTransfers', []):
                    if tr['toUserAccount'] == CONFIG["HOT_WALLET"]:
                        memo_raw = tx.get('instructions', [{}])[0].get('parsed', {}).get('info', {}).get('memo', "")
                        if memo_raw.isdigit():
                            amt = tr['amount'] / 10**9
                            tier = "WHALE" if amt >= CONFIG["TOLL_WHALE"] else "BASIC"
                            # Grant 30-day access
                            r.set(f"access:{memo_raw}", tier, ex=2592000)
                            Ledger.log_event(memo_raw, "PAYMENT", {"amt": amt, "tier": tier})
                            bot.send_message(memo_raw, f"✅ **{tier} ACCESS GRANTED**\nProfit Routed: {CONFIG['KRAKEN_SETTLEMENT'][:6]}...")
    return jsonify({"status": "ok"}), 200

# --- 4. COMMAND HANDLERS ---
@bot.message_handler(commands=['stats'])
def show_god_view(message):
    if str(message.from_user.id) != CONFIG["ADMIN"]: return
    rev = r.get("total_rev") or 0
    subs = len(r.keys("access:*"))
    logs = r.xrevrange("protocol_logs", count=5)
    msg = (f"👑 **DASHBOARD**\n💰 Lifetime Rev: `{rev} SOL`\n👥 Active Subs: `{subs}`\n🏛️ Destination: `Kraken`")
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['health'])
def health_check(message):
    bot.reply_to(message, "🛡️ **S.I.P. ONLINE**\nMode: Webhook v12.2\nStatus: Sovereign")

@bot.message_handler(commands=['scrape'])
def hunter(message):
    uid = str(message.from_user.id)
    if uid != CONFIG["ADMIN"] and not r.get(f"access:{uid}"):
        return bot.reply_to(message, "🚫 **ACCESS DENIED**\nPlease pay toll.")
    bot.reply_to(message, "📡 **SCANNING MAINNET...**\nHunting Liquidity Pairs.")

# --- 5. RENDER STABILITY FIXES ---
@app.route('/')
def health_ping():
    # Crucial: Gives Render a "success" response so it doesn't time out
    return "S.I.P. v12.2: Live", 200

if __name__ == "__main__":
    # Crucial: Dynamically binds to whatever port Render provides
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
