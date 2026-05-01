/* ==========================================================
 * S.I.P. OMNICORE v35.5 - TITAN SHIELD (OVERLAP EDITION)
 * ========================================================== */

require('dotenv').config();
const { Connection, Keypair, VersionedTransaction } = require('@solana/web3.js');
const axios = require('axios');
const TelegramBot = require('node-telegram-bot-api');
const bs58 = require('bs58');
const http = require('http');

const CONFIG = {
    TOKEN: process.env.TELEGRAM_BOT_TOKEN,
    CHAT: process.env.TELEGRAM_ADMIN_ID,
    RPC: process.env.RPC_URL,
    KEY: process.env.PRIVATE_KEY,
    PORT: process.env.PORT || 10000,
    JITO_FEE: parseInt(process.env.JITO_TIP_AMOUNT) || 100000,
    MIN_OUT: parseInt(process.env.CONFIDENCE_THRESHOLD) || 108000000,
    ENABLED: process.env.ACTIVE === 'true'
};

const connection = new Connection(CONFIG.RPC, 'confirmed');
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));

// Initialize bot WITHOUT polling initially to avoid 409 Conflict
const bot = new TelegramBot(CONFIG.TOKEN, { polling: false });

let hunting = CONFIG.ENABLED;
let strikes = 0;

// 120s Overlap Logic: Graceful Shutdown
process.on('SIGTERM', async () => {
    console.log("[SYSTEM] SIGTERM received. Cleaning up for overlap...");
    hunting = false; // Stop predator loop
    if (bot.isPolling()) await bot.stopPolling();
    setTimeout(() => process.exit(0), 2000); // Give it a 2s window to breathe
});

// Titan Shield Keep-Alive & Health Check Gate
const server = http.createServer((req, res) => {
    if (req.url === '/health') {
        // Render hits this. Once it returns 200, Render starts the 120s swap.
        if (!bot.isPolling()) {
            console.log("[SYSTEM] Health check passed. Starting Telegram Polling...");
            bot.startPolling({ interval: 300 });
        }
        res.writeHead(200);
        res.end('HEALTHY');
    } else {
        res.writeHead(200);
        res.end('V35.5_TITAN_ALIVE');
    }
}).listen(CONFIG.PORT);

async function predator() {
    console.log("[SYSTEM] Titan Shield Engaged. Waiting for Health Gate...");
    while (true) {
        if (hunting && bot.isPolling()) {
            try {
                // ... (Your predator scan logic here)
            } catch (e) { 
                if (e.response?.status === 429) await new Promise(r => setTimeout(r, 2000));
            }
        }
        await new Promise(r => setTimeout(r, 1000));
    }
}

// (Commands /status, /shield_on, /shield_off stay the same)

predator().catch(err => {
    console.error("FATAL", err);
    process.exit(1);
});
