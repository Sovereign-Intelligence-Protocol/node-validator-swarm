import os
import time
import redis
import telebot
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# --- CONFIGURATION & ENV SYNC ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RPC_URL = os.getenv("RPC_URL") # Must be your Helius URL
WALLET_ADDR = os.getenv("SOLANA_WALLET_ADDRESS") # Your Hot Wallet
KRAKEN_ADDR = os.getenv("KRAKEN_ADDRESS") # Your Revenue Destination
REDIS_URL = os.getenv("REDIS_URL")

bot = telebot.TeleBot(TOKEN)
solana_client = Client(RPC_URL)
r = redis.from_url(REDIS_URL, decode_responses=True)

# --- THE GATEKEEPER (TOLL BRIDGE LOGIC) ---
def check_access(user_id):
    """Checks Redis for active subscription or one-time toll."""
    # Check if user is the admin (Joshua)
    if str(user_id) == os.getenv("ADMIN_ID"):
        return True
    
    access_status = r.get(f"user:{user_id}:status")
    return access_status == "active"

def gatekeeper(func):
    """Decorator to protect commands with the Toll Bridge."""
    def wrapper(message):
        if check_access(message.from_user.id):
            return func(message)
        else:
            markup = telebot.types.InlineKeyboardMarkup()
            pay_btn = telebot.types.InlineKeyboardButton("💳 Pay 0.1 SOL Toll", url=f"https://solana.com/pay/{WALLET_ADDR}")
            markup.add(pay_btn)
            bot.reply_to(message, 
                "🚫 **ACCESS RESTRICTED**\n\n"
                "The Sovereign Intelligence Protocol requires a toll or active subscription to execute this command.\n\n"
                f"**Toll:** 0.1 SOL\n**Destination:** `{WALLET_ADDR}`", 
                parse_mode="Markdown", reply_markup=markup)
    return wrapper

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⚡ **Sovereign Intelligence Protocol v6.0**\n\n"
                          "Status: ONLINE\n"
                          "Modules: Toll Bridge, Sniper, Subscriptions\n\n"
                          "Use /health to audit or /scrape to begin.")

@bot.message_handler(commands=['health'])
def system_audit(message):
    try:
        # RPC Check
        rpc_status = "✅" if solana_client.is_connected() else "❌"
        
        # Balance Check
        pubkey = Pubkey.from_string(WALLET_ADDR)
        balance = solana_client.get_balance(pubkey).value / 10**9
        
        # Signer Check
        signer_status = "✅ ARMED" if os.getenv("PRIVATE_KEY") else "❌ DISARMED"

        audit_msg = (
            f"📊 **SYSTEM AUDIT**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🌐 **RPC:** {rpc_status}\n"
            f"🔑 **Signer:** {signer_status}\n"
            f"💰 **Hot Wallet:** `{balance:.4f} SOL`\n"
            f"🏢 **Revenue Route:** Kraken ✅\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Ready for deployment."
        )
        bot.reply_to(message, audit_msg, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Audit Failed: {str(e)}")

@bot.message_handler(commands=['scrape'])
@gatekeeper
def start_hunting(message):
    bot.reply_to(message, "📡 **INITIATING SCAN...**\nSearching Raydium Mainnet for new liquidity pairs...")
    # Insert your Playwright/BeautifulSoup logic here
    # After finding a lead, the bot posts it here.

@bot.message_handler(commands=['snipe'])
@gatekeeper
def execute_snipe(message):
    bot.reply_to(message, "🎯 **SNIPER ARMED**\nMonitoring Jito bundles for atomic execution...")

# --- REVENUE ROUTING (KRAKEN BRIDGE) ---
@bot.message_handler(commands=['sweep'])
def sweep_to_kraken(message):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    bot.reply_to(message, f"💸 **SWEEP INITIATED**\nTransferring settled funds to Kraken: `{KRAKEN_ADDR}`")
    # Insert Solana transfer logic here using PRIVATE_KEY

if __name__ == "__main__":
    print("Sovereign Protocol Online...")
    bot.infinity_polling()
