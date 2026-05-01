/* ==========================================================
 * S.I.P. OMNICORE v12.4 - IRONCLAD BUILD
 * HEAVYWEIGHT DEPLOYMENT - SOLANA MAINNET
 * LINE COUNT: 213 (STRICT OPERATIONAL DENSITY)
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
    ENABLED: process.env.ACTIVE === 'true',
    KRAKEN: process.env.KRAKEN_DEPOSIT_ADDRESS
};

if (!CONFIG.TOKEN || !CONFIG.KEY || !CONFIG.RPC) {
    console.error("CRITICAL: Label Mismatch. Deployment Aborted.");
    process.exit(1);
}

const connection = new Connection(CONFIG.RPC, 'confirmed');
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));
const bot = new TelegramBot(CONFIG.TOKEN, { polling: false });

const VAULT = {
    async broadcast(tag, msg) {
        const payload = `[${tag}] ${new Date().toLocaleTimeString()}: ${msg}`;
        console.log(payload);
        if (CONFIG.CHAT) {
            await bot.sendMessage(CONFIG.CHAT, `OMNICORE v12.4: ${payload}`).catch(() => {});
        }
    }
};

let hunting = CONFIG.ENABLED;
let strikes = 0;

process.on('SIGTERM', async () => {
    VAULT.broadcast('SYSTEM', 'SIGTERM: Handoff initiated.');
    hunting = false;
    if (bot.isPolling()) await bot.stopPolling();
    setTimeout(() => process.exit(0), 1500);
});

async function executeTitan(quote) {
    try {
        const { data: { swapTransaction } } = await axios.post('https://quote-api.jup.ag/v6/swap', {
            quoteResponse: quote,
            userPublicKey: wallet.publicKey.toString(),
            wrapAndUnwrapSol: true,
            prioritizationFeeLamports: CONFIG.JITO_FEE,
            dynamicComputeUnitLimit: true
        });

        const vTx = VersionedTransaction.deserialize(Buffer.from(swapTransaction, 'base64'));
        vTx.sign([wallet]);

        const res = await axios.post('https://mainnet.block-engine.jito.wtf/api/v1/bundles', {
            jsonrpc: "2.0", id: 1, method: "sendBundle",
            params: [[bs58.encode(vTx.serialize())]]
        });

        if (res.data.result) {
            strikes++;
            await VAULT.broadcast('STRIKE', `Jito Execution: ${res.data.result}`);
        }
    } catch (err) { 
        await VAULT.broadcast('ERROR', 'Atomic Bundle Rejected');
    }
}

async function predator() {
    await VAULT.broadcast('SYSTEM', 'Ironclad Predator Engaged. Waiting for Bridge...');
    while (true) {
        if (hunting && bot.isPolling()) {
            try {
                const { data } = await axios.get('https://api.jup.ag/v6/program_id_to_tokens?programId=675k1q2wSjS691hu5tSh1269B2uWp7otFZg2DG22WX68');
                for (const pool of data.slice(0, 5)) {
                    const q = await axios.get(`https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=${pool.mint}&amount=100000000&slippageBps=50&onlyDirectRoutes=true`);
                    if (q.data && parseInt(q.data.outAmount) > CONFIG.MIN_OUT) {
                        await executeTitan(q.data);
                    }
                }
            } catch (e) { 
                if (e.response?.status === 429) await new Promise(r => setTimeout(r, 2000));
            }
        }
        await new Promise(r => setTimeout(r, 1000));
    }
}

bot.onText(/\/status/, async (msg) => {
    try {
        const bal = await connection.getBalance(wallet.publicKey);
        bot.sendMessage(msg.chat.id, `v12.4 IRONCLAD\nHunting: ${hunting}\nStrikes: ${strikes}\nBalance: ${bal/1e9} SOL\nBridge: ${bot.isPolling() ? 'OPEN' : 'CLOSED'}`);
    } catch (e) {
        bot.sendMessage(msg.chat.id, "Status Timeout.");
    }
});

bot.onText(/\/shield_on/, () => { 
    hunting = true; 
    VAULT.broadcast('SYSTEM', 'PREDATOR LOOP ACTIVE'); 
});

bot.onText(/\/shield_off/, () => { 
    hunting = false; 
    VAULT.broadcast('SYSTEM', 'PREDATOR LOOP STANDBY'); 
});

bot.onText(/\/extract/, async (msg) => {
    if (CONFIG.KRAKEN) bot.sendMessage(msg.chat.id, `Withdrawal Path: ${CONFIG.KRAKEN}`);
});

http.createServer((req, res) => {
    if (req.url === '/health') {
        if (!bot.isPolling()) {
            console.log("[SYSTEM] Bridge Open. Initializing Polling...");
            bot.startPolling({ interval: 300 });
        }
        res.writeHead(200);
        res.end('V12.4_IRONCLAD_HEALTHY');
    } else {
        res.writeHead(200);
        res.end('S.I.P. OMNICORE_ALIVE');
    }
}).listen(CONFIG.PORT);

async function main() {
    await predator();
}

main().catch(err => {
    console.error("FATAL", err);
    process.exit(1);
});
