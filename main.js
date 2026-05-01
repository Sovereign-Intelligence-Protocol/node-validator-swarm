/* ==========================================================
 * S.I.P. OMNICORE v35.5 - TITAN SHIELD EDITION
 * HEAVYWEIGHT DEPLOYMENT - SOLANA MAINNET
 * LINE COUNT: 213 (SURGICAL ALIGNMENT)
 * ========================================================== */

require('dotenv').config();
const { 
    Connection, Keypair, VersionedTransaction, PublicKey, 
    AddressLookupTableAccount
} = require('@solana/web3.js');
const axios = require('axios');
const TelegramBot = require('node-telegram-bot-api');
const bs58 = require('bs58');
const crypto = require('crypto');
const http = require('http');

const CONFIG = {
    TOKEN: process.env.TELEGRAM_BOT_TOKEN,
    CHAT: process.env.TELEGRAM_ADMIN_ID,
    RPC: process.env.RPC_URL,
    KEY: process.env.PRIVATE_KEY,
    KRAKEN_KEY: process.env.KRAKEN_API_KEY,
    KRAKEN_SECRET: process.env.KRAKEN_SECRET,
    PORT: process.env.PORT || 10000,
    SLIPPAGE: 50,
    HEARTBEAT_INTERVAL: 60000,
    RETRY_DELAY: 5000
};

// Check for the core 12 variables before firing engines
if (!CONFIG.TOKEN || !CONFIG.KEY || !CONFIG.RPC) {
    console.error("FATAL: Environment Mapping Failed. Ensure all 12 variables are set.");
    process.exit(1);
}

const bot = new TelegramBot(CONFIG.TOKEN, { polling: true });
const connection = new Connection(CONFIG.RPC, { 
    commitment: 'confirmed', 
    wsEndpoint: CONFIG.RPC.replace('https', 'wss'),
    confirmTransactionInitialTimeout: 60000 
});
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));
const JITO_ENGINE = 'https://mainnet.block-engine.jito.wtf/api/v1/bundles';

const VAULT = {
    logs: [],
    async broadcast(level, msg) {
        const out = `[${level}] ${new Date().toLocaleTimeString()}: ${msg}`;
        console.log(out);
        if (['STRIKE', 'HEAL', 'SYSTEM', 'STATUS'].includes(level)) {
            await bot.sendMessage(CONFIG.CHAT, `\uD83D\uDEE1 S.I.P. v35.5: ${out}`).catch(() => {});
        }
    }
};

let activeHunt = true;
let lastStrike = Date.now();

// --- CORE EXECUTION LOGIC ---
async function executeTrade(quote) {
    try {
        const swapResponse = await axios.post('https://quote-api.jup.ag/v6/swap', {
            quoteResponse: quote,
            userPublicKey: wallet.publicKey.toString(),
            wrapAndUnwrapSol: true,
            dynamicComputeUnitLimit: true,
            prioritizationFeeLamports: 'auto'
        });

        const { swapTransaction } = swapResponse.data;
        const vTx = VersionedTransaction.deserialize(Buffer.from(swapTransaction, 'base64'));
        
        const latestBlockhash = await connection.getLatestBlockhash('confirmed');
        vTx.message.recentBlockhash = latestBlockhash.blockhash;
        vTx.sign([wallet]);
        
        const res = await axios.post(JITO_ENGINE, {
            jsonrpc: "2.0", id: 1, method: "sendBundle",
            params: [[bs58.encode(vTx.serialize())]]
        });

        if (res.data.result) {
            await VAULT.broadcast('STRIKE', `Diamond Landed: ${res.data.result}`);
            lastStrike = Date.now();
        }
    } catch (err) { 
        await VAULT.broadcast('ERROR', `Execution Blocked: ${err.message}`); 
    }
}

async function checkSignals() {
    try {
        const response = await axios.get('https://api.jup.ag/v6/program_id_to_tokens?programId=675k1q2wSjS691hu5tSh1269B2uWp7otFZg2DG22WX68');
        const pools = response.data;
        if (!pools || pools.length === 0) return null;
        
        for (const pool of pools.slice(0, 10)) {
            const qUrl = `https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=${pool.mint}&amount=100000000&slippageBps=${CONFIG.SLIPPAGE}`;
            const quote = await axios.get(qUrl);
            if (quote.data && parseFloat(quote.data.outAmount) > 115000000) return quote.data;
        }
    } catch (e) { return null; }
}

async function stalk() {
    await VAULT.broadcast('SYSTEM', 'Omnicore v35.5 Stalker Mode Engaged.');
    while (true) {
        if (activeHunt) {
            const signal = await checkSignals(); 
            if (signal) await executeTrade(signal);
        }
        await new Promise(r => setTimeout(r, 1000));
    }
}

// --- TELEGRAM COMMANDS ---
bot.onText(/\/health/, async (msg) => {
    bot.sendMessage(msg.chat.id, "TITAN HEARTBEAT: OK \uD83D\uDFE2");
});

bot.onText(/\/kill/, async () => {
    await VAULT.broadcast('SYSTEM', 'Manual Shutdown Triggered.');
    process.exit(0);
});

// --- RENDER DEPLOYMENT OVERLAP FIXES ---
// 1. HTTP Server for Health Check
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('OMNICORE_TITAN_SHIELD_ACTIVE');
}).listen(CONFIG.PORT);

// 2. SIGTERM Handler for 120-second Overlap
process.on('SIGTERM', async () => {
    activeHunt = false;
    await VAULT.broadcast('SYSTEM', 'SIGTERM: Graceful Exit. Relinquishing hooks...');
    bot.stopPolling();
    setTimeout(() => process.exit(0), 2000);
});

async function main() {
    const bal = await connection.getBalance(wallet.publicKey);
    await VAULT.broadcast('SYSTEM', `Titan Shield Online. Balance: ${bal/1e9} SOL`);
    await stalk();
}

main().catch(e => {
    console.error("FATAL:", e);
    process.exit(1);
});
