import os, time, redis, telebot, threading, requests
from flask import Flask, request, jsonify
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# --- CORE SETTINGS (The Only Part You Ever Edit) ---
CONFIG = {
    "TOLL_BASIC": 0.1,
    "TOLL_WHALE": 0.5,
    "SWEEP_THRESHOLD": 1.5,
    "REVENUE_CH": os.getenv("REVENUE_CHANNEL_ID"),
    "ADMIN": os.getenv("ADMIN_ID"),
    "HOT_WALLET": os.getenv("SOLANA_WALLET_ADDRESS")
}

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
app = Flask(__name__)

# --- 1. INTELLIGENCE & TELEMETRY ENGINE ---
class Ledger:
    @staticmethod
    def log_event(uid, event, meta=None):
        """Total Protocol Audit: Tracks Conversion, Churn, and Usage."""
        entry = {"uid": str(uid), "event": event, "ts": time.time(), "meta": str(meta)}
        r.xadd("protocol_logs", entry, maxlen=10000)
        r.hset(f"u:{uid}", "last_act", time.time())
        if event == "PAYMENT":
            r.incrbyfloat("total_rev", meta.get("amt", 0))

# --- 2. AUTOMATED REVENUE & GATEKEEPER ---
@app.route('/helius-webhook', methods=['POST'])
def gatekeeper():
    data = request.json
    for tx in data:
        if tx.get('type') == 'TRANSFER':
            for tr in tx.get('nativeTransfers', []):
                if tr['toUserAccount'] == CONFIG["HOT_WALLET"]:
                    uid = tx.get('instructions', [{}])[0].get('parsed', {}).get('info', {}).get('memo')
                    amt = tr['amount'] / 10**9
                    if uid and uid.isdigit():
                        tier = "WHALE" if amt >= CONFIG["TOLL_WHALE"] else "BASIC"
                        r.set(f"access:{uid}", tier, ex=2592000) # 30 Days
                        Ledger.log_event(uid, "PAYMENT", {"amt": amt, "tier": tier})
                        bot.send_message(uid, f"✅ **{tier} ACCESS GRANTED**\nHunting license active.")
    return jsonify({"status": "ok"}), 200

# --- 3. THE MASTER COMMANDS ---
@bot.message_handler(commands=['stats'])
def show_god_view(message):
    if str(message.from_user.id) != CONFIG["ADMIN"]: return
    rev = r.get("total_rev") or 0
    subs = len(r.keys("access:*"))
    logs = r.xrevrange("protocol_logs", count=5)
    
    msg = (f"👑 **OMNI-SOVEREIGN DASHBOARD**\n"
           f"💰 Lifetime Rev: `{rev} SOL`\n"
           f"👥 Active Subs: `{subs}`\n\n"
           f"🛰️ **Real-Time Audit:**\n")
    for _, l in logs:
        msg += f"• {l['uid']} | {l['event']} | {l['meta']}\n"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['scrape'])
def hunter(message):
    uid = str(message.from_user.id)
    access = r.get(f"access:{uid}")
    if uid != CONFIG["ADMIN"] and not access:
        # Auto-generate Payment Link
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💳 Pay 0.1 SOL", url=f"https://solana.com/pay/{CONFIG['HOT_WALLET']}?amount=0.1&memo={uid}"))
        return bot.reply_to(message, "🚫 **ACCESS DENIED**\nPay toll to unlock sniper.", reply_markup=markup)
    
    Ledger.log_event(uid, "SCRAPE_START", {"tier": access or "ADMIN"})
    bot.reply_to(message, f"📡 **SCANNING... (Tier: {access or 'ADMIN'})**")

# --- 4. STARTUP PROTOCOL ---
if __name__ == "__main__":
    # Self-Updating Commands UI
    bot.set_my_commands([
        telebot.types.BotCommand("health", "🛡️ Security Audit"),
        telebot.types.BotCommand("scrape", "📡 Start Lead Hunt"),
        telebot.types.BotCommand("stats", "📊 Master Stats"),
        telebot.types.BotCommand("balance", "💰 Wallet Balance")
    ])
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    print("S.I.P. v12.0 'Omni-Sovereign' is Online.")
    bot.infinity_polling()
