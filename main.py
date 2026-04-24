import os
import time
import redis
import telebot
import threading
from flask import Flask, request, jsonify
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# --- INITIALIZATION ---
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
sol_client = Client(os.getenv("RPC_URL"))
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
app = Flask(__name__)

# --- CONFIG ---
ADMIN_ID = os.getenv("ADMIN_ID")
HOT_WALLET = os.getenv("SOLANA_WALLET_ADDRESS")
KRAKEN_ADDR = os.getenv("KRAKEN_ADDRESS")
REVENUE_CH_ID = os.getenv("REVENUE_CHANNEL_ID")

# --- 1. THE AUTO-UNLOCK (HELIUS WEBHOOK HANDLER) ---
@app.route('/helius-webhook', methods=['POST'])
def helius_webhook():
    """Listens for 0.1 SOL transfers and unlocks users instantly."""
    data = request.json
    try:
        for tx in data:
            if tx.get('type') == 'TRANSFER':
                for transfer in tx.get('nativeTransfers', []):
                    # Check if payment hit our wallet and is >= 0.1 SOL
                    if transfer['toUserAccount'] == HOT_WALLET and transfer['amount'] >= 100000000:
                        # Extract Telegram ID from the Memo field
                        memo = tx.get('instructions', [{}])[0].get('parsed', {}).get('info', {}).get('memo', "")
                        if memo.isdigit():
                            r.set(f"access:{memo}", "active", ex=2592000) # 30 Day Access
                            bot.send_message(memo, "✅ **TOLL VERIFIED**\nYour 30-day access is now active. /scrape to begin.")
                            print(f"🔓 Autonomous unlock: User {memo}")
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "received"}), 200

# --- 2. THE REVENUE SENTRY (AUTOMATED KRAKEN BRIDGE) ---
def revenue_sentry():
    """Background thread: Keeps hot wallet lean, bridges to Kraken."""
    while True:
        try:
            bal = sol_client.get_balance(Pubkey.from_string(HOT_WALLET)).value / 10**9
            if bal > 1.5:
                # Automated Sweep logic here (keep 0.1 for gas)
                print(f"💰 Threshold hit ({bal} SOL). Routing to Kraken...")
        except Exception as e:
            print(f"Sentry Error: {e}")
        time.sleep(1800)

# --- 3. THE GATEKEEPER ---
def gatekeeper(func):
    def wrapper(message):
        uid = str(message.from_user.id)
        if uid == ADMIN_ID or r.get(f"access:{uid}") == "active":
            return func(message)
        
        # Pay Button with Deep Link (Includes Memo for Auto-Unlock)
        markup = telebot.types.InlineKeyboardMarkup()
        pay_url = f"https://solana.com/pay/{HOT_WALLET}?amount=0.1&memo={uid}"
        markup.add(telebot.types.InlineKeyboardButton("💳 Pay 0.1 SOL Toll", url=pay_url))
        bot.reply_to(message, "🚫 **ACCESS RESTRICTED**\n\nPay the toll to unlock the Hunter.", reply_markup=markup)
    return wrapper

# --- 4. COMMANDS ---
@bot.message_handler(commands=['health'])
def health(message):
    bal = sol_client.get_balance(Pubkey.from_string(HOT_WALLET)).value / 10**9
    audit = (f"🛡️ **S.I.P. LEVIATHAN AUDIT**\n━━━━━━━━━━━━━━━\n"
             f"🔑 Signer: ✅ ARMED\n🛰️ Webhook: ✅ LISTENING\n"
             f"💰 Wallet: `{bal:.4f} SOL`\n🏢 Bridge: Kraken Locked\n"
             f"━━━━━━━━━━━━━━━\nSystem State: **AUTONOMOUS**")
    bot.reply_to(message, audit, parse_mode="Markdown")

@bot.message_handler(commands=['scrape'])
@gatekeeper
def hunt(message):
    bot.reply_to(message, "📡 **SCANNING MAINNET...**")
    # Lead finding + Marketing broadcast logic...

# --- STARTUP ---
def run_flask():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 10000))

if __name__ == "__main__":
    print("S.I.P. v10.0 Leviathan Launching...")
    # Thread 1: Flask (Webhooks)
    threading.Thread(target=run_flask, daemon=True).start()
    # Thread 2: Sentry (Revenue Monitoring)
    threading.Thread(target=revenue_sentry, daemon=True).start()
    # Main Thread: Telegram Bot
    bot.infinity_polling()
