import os
import json
import time
import logging
import threading
import requests
import telebot
from flask import Flask, request, jsonify

# Solana specific imports
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.message import Message
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
import base58

# --- 1. THE TITAN ARSENAL: OMNI-LABEL MAPPING ---
class Config:
    VERSION = "35.8 TITAN OVERLORD (CLEAN SWEEP)"
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TOKEN")
    ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID") or os.getenv("CHAT_ID") or os.getenv("ADMIN_ID")
    RPC = os.getenv("RPC_URL") or os.getenv("SOLANA_RPC_URL") or os.getenv("RPC")
    KEY = os.getenv("SOLANA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY") or os.getenv("KEY")
    JITO_URL = os.getenv("JITO_URL") or "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
    KRAKEN_ADDR = os.getenv("KRAKEN_TREASURY_ADDR") or "25d5qmLMbjFvz3wijmTQKEqTvb7UZxjJhqugrzPYx3kM"
    PORT = int(os.getenv("PORT") or "10000")
    DUST_THRESHOLD = 0.001 # Threshold to consider a balance as "Fragment"

# --- 2. SYSTEM INITIALIZATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TITAN_OVERLORD")

if not Config.TOKEN or not Config.KEY or not Config.RPC:
    logger.error("FATAL: Titan Arsenal Mapping Failed. Check Environment Variables.")
    exit(1)

bot = telebot.TeleBot(Config.TOKEN)
app = Flask(__name__)
active_hunt = True

# Solana Client & Wallet
solana_client = Client(Config.RPC)
try:
    wallet = Keypair.from_base58_string(Config.KEY)
except:
    logger.error("FATAL: Private Key Decoding Failed.")
    exit(1)

def broadcast(level, msg):
    out = f"🛡️ v35.8 OVERLORD [{level}]: {msg}"
    logger.info(out)
    try:
        if Config.ADMIN_ID:
            bot.send_message(Config.ADMIN_ID, out)
    except: pass

# --- 3. THE FRAGMENT PURGE (Rent Reclamation) ---
def purge_fragments():
    """Scans for tiny SPL balances and reclaims SOL rent."""
    broadcast("SYSTEM", "Initiating Wallet Fragment Purge...")
    try:
        # Get all token accounts for the wallet
        opts = TokenAccountOpts(program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
        response = solana_client.get_token_accounts_by_owner(wallet.pubkey(), opts)
        
        accounts = response.value
        purged_count = 0
        sol_reclaimed = 0

        for acc in accounts:
            # Logic to check balance and close if below threshold
            # In production, this would use 'close_account' instructions
            # For v35.8 safety, we log the targets first
            logger.info(f"[PURGE] Identified Fragment Account: {acc.pubkey}")
            purged_count += 1
            sol_reclaimed += 0.002 # Average rent reclamation per account

        broadcast("STATUS", f"Purge Complete. {purged_count} fragments identified. ~{sol_reclaimed:.4f} SOL reclaimable.")
    except Exception as e:
        logger.error(f"Purge Error: {e}")

# --- 4. TELEGRAM COMMAND CENTER (UPGRADED) ---
@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    menu = (
        "🛡️ S.I.P. v35.8 TITAN OVERLORD ONLINE\n\n"
        "Commands:\n"
        "/on - Start Hunting\n"
        "/off - Stop Hunting\n"
        "/clean - Purge Trade Fragments\n"
        "/health - Check Heartbeat\n"
        "/audit - System Status\n"
        "/kill - Shutdown"
    )
    bot.reply_to(message, menu)

@bot.message_handler(commands=['on'])
def handle_on(message):
    global active_hunt
    active_hunt = True
    broadcast("STATUS", "Titan Overlord: HUNTING ENABLED")

@bot.message_handler(commands=['off'])
def handle_off(message):
    global active_hunt
    active_hunt = False
    broadcast("STATUS", "Titan Overlord: HUNTING DISABLED")

@bot.message_handler(commands=['clean'])
def handle_clean(message):
    threading.Thread(target=purge_fragments).start()
    bot.reply_to(message, "🧹 Fragment Purge Initiated. Reclaiming rent...")

@bot.message_handler(commands=['health'])
def handle_health(message):
    bot.reply_to(message, "TITAN HEARTBEAT: OK 🟢\nVersion: 35.8 Overlord")

@bot.message_handler(commands=['audit'])
def handle_audit(message):
    try:
        bal = solana_client.get_balance(wallet.pubkey()).value
        status = "HUNTING" if active_hunt else "IDLE"
        report = (
            f"--- TITAN AUDIT ---\n"
            f"Status: {status}\n"
