/* ==========================================================
 * S.I.P. OMNICORE v12.4 - SOVEREIGN COMMAND
 * HEAVYWEIGHT DEPLOYMENT - SOLANA MAINNET
 * LINE COUNT: 213 (STRICT ALIGNMENT)
 * ========================================================== */

require('dotenv').config();
const { 
    Connection, Keypair, VersionedTransaction, PublicKey, 
    TransactionMessage, AddressLookupTableAccount 
} = require('@solana/web3.js');
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
    MIN_PROFIT: 0.05,
    SLIPPAGE: 50
};

// Polling fix: Force immediate connection reset
const bot = new TelegramBot(CONFIG.TOKEN, { 
    polling: { 
        autoStart: true,
        params: { timeout: 10 } 
    } 
});

const connection = new Connection(CONFIG.RPC, { commitment: 'confirmed' });
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));

const VAULT = {
    async broadcast(level, msg) {
        const out = `[${level}] ${new Date().toLocaleTimeString()}: ${msg}`;
        console.log(out);
        if (CONFIG.CHAT) {
            await bot.sendMessage(CONFIG.CHAT, `Omnicore v12.4: ${out}`).catch(e => console.error("Broadcast Error:", e.message));
        }
    }
};

let activeHunt = true;

async function executeTrade(quote) {
    try {
        const swapResponse = await axios.post('https://quote-api.jup.ag/v6/swap', {
            quoteResponse: quote,
            userPublicKey: wallet.publicKey.toString(),
            wrapAndUnwrapSol: true,
            dynamicComputeUnitLimit: true,
            prioritizationFeeLamports: 'auto'
        });
        const vTx = VersionedTransaction.deserialize(Buffer.from(swapResponse.data.swapTransaction, 'base64'));
        vTx.sign([wallet]);
        const res = await axios.post('https://mainnet.block-engine.jito.wtf/api/v1/bundles', {
            jsonrpc: "2.0", id: 1, method: "sendBundle",
            params: [[bs58.encode(vTx.serialize())]]
        });
        if (res.data.result) await VAULT.broadcast('STRIKE', `Trade ID: ${res.data.result}`);
    } catch (err) { console.error("Trade Logic Error"); }
}

async function stalk() {
    while (true) {
        if (activeHunt) {
            try {
                const response = await axios.get('https://api.jup.ag/v6/program_id_to_tokens?programId=675k1q2wSjS691hu5tSh1269B2uWp7otFZg2DG22WX68');
                const pools = response.data?.slice(0, 5);
                for (const pool of pools) {
                    const qUrl = `https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=${pool.mint}&amount=100000000&slippageBps=${CONFIG.SLIPPAGE}`;
                    const quote = await axios.get(qUrl);
                    if (quote.data && parseFloat(quote.data.outAmount) > 110000000) await executeTrade(quote.data);
                }
            } catch (e) { }
        }
        await new Promise(r => setTimeout(r, 2000));
    }
}

bot.onText(/\/status/, (msg) => {
    bot.sendMessage(msg.chat.id, `v12.4 LIVE\nHunt: ${activeHunt}\nUptime: ${Math.floor(process.uptime()/60)}m`);
});

bot.on('polling_error', (error) => {
    if (error.code === 'ETELEGRAM' && error.message.includes('401')) {
        console.error("CRITICAL: Telegram Token Rejected. Check Render Environment Variables.");
    }
});

http.createServer((req, res) => {
    res.writeHead(200);
    res.end('ALIVE');
}).listen(CONFIG.PORT);

async function main() {
    await VAULT.broadcast('SYSTEM', 'Sovereign Command Online.');
    stalk();
}

main();
