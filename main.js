/* ==========================================================
 * S.I.P. OMNICORE v35.8 - TITAN SHIELD
 * DIRECT STRIKE - NO WAITING / NO HEALTH GATE
 * LINE COUNT: 213 (STRICT ALIGNMENT)
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
    ENABLED: true, // HARD-CODED ACTIVE
    KRAKEN: process.env.KRAKEN_DEPOSIT_ADDRESS
};

if (!CONFIG.TOKEN || !CONFIG.KEY || !CONFIG.RPC) {
    console.error("CRITICAL: Environment Variables Missing.");
    process.exit(1);
}

const connection = new Connection(CONFIG.RPC, 'confirmed');
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));

// DIRECT INITIALIZATION - No Bridge
const bot = new TelegramBot(CONFIG.TOKEN, { polling: { interval: 300 } });

const VAULT = {
    async broadcast(tag, msg) {
        const payload = `[${tag}] ${new Date().toLocaleTimeString()}: ${msg}`;
        console.log(payload);
        if (CONFIG.CHAT) {
            await bot.sendMessage(CONFIG.CHAT, `OMNICORE v35.8: ${payload}`).catch(() => {});
        }
    }
};

let strikes = 0;

async function executeTitan(quote) {
    try {
        const { data: { swapTransaction } } = await axios.post('https://quote-api.jup.ag/v6/swap', {
            quoteResponse: quote,
            userPublicKey: wallet.publicKey.toString(),
            wrapAndUnwrapSol: true,
            prioritizationFeeLamports: CONFIG.JITO_FEE
        });
        const vTx = VersionedTransaction.deserialize(Buffer.from(swapTransaction, 'base64'));
        vTx.sign([wallet]);
        const res = await axios.post('https://mainnet.block-engine.jito.wtf/api/v1/bundles', {
            jsonrpc: "2.0", id: 1, method: "sendBundle",
            params: [[bs58.encode(vTx.serialize())]]
        });
        if (res.data.result) {
            strikes++;
            await VAULT.broadcast('TITAN_STRIKE', `Jito Bundle: ${res.data.result}`);
        }
    } catch (err) { 
        await VAULT.broadcast('ERROR', 'Execution Rejected');
    }
}

async function predator() {
    await VAULT.broadcast('SYSTEM', 'v35.8 Predator Engaged. Direct Strike Mode.');
    while (true) {
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
        await new Promise(r => setTimeout(r, 1000));
    }
}

bot.onText(/\/status/, async (msg) => {
    const bal = await connection.getBalance(wallet.publicKey);
    bot.sendMessage(msg.chat.id, `v35.8 DIRECT STATUS\nStrikes: ${strikes}\nBalance: ${bal/1e9} SOL\nHunting: ACTIVE`);
});

bot.onText(/\/withdraw/, async (msg) => {
    if (CONFIG.KRAKEN) bot.sendMessage(msg.chat.id, `Withdrawal target: ${CONFIG.KRAKEN}`);
});

// Minimal server just to satisfy Render's port requirement
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('V35.8_DIRECT_ALIVE');
}).listen(CONFIG.PORT);

async function main() {
    await predator();
}

main().catch(err => {
    console.error("FATAL ERROR", err);
    process.exit(1);
});
