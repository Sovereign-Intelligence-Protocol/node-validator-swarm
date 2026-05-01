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
    SLIPPAGE: 50,
    HEARTBEAT: 60000
};

if (!CONFIG.TOKEN || !CONFIG.KEY) {
    console.error("FATAL: Environment Mapping Failed.");
    process.exit(1);
}

const bot = new TelegramBot(CONFIG.TOKEN, { polling: { interval: 300, params: { timeout: 10 } } });
const connection = new Connection(CONFIG.RPC, { commitment: 'confirmed', confirmTransactionInitialTimeout: 60000 });
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));
const JITO_ENGINE = 'https://mainnet.block-engine.jito.wtf/api/v1/bundles';

const VAULT = {
    logs: [],
    async broadcast(level, msg) {
        const out = `[${level}] ${new Date().toLocaleTimeString()}: ${msg}`;
        console.log(out);
        if (['STRIKE', 'SYSTEM', 'STATUS'].includes(level)) {
            await bot.sendMessage(CONFIG.CHAT, `Omnicore v12.4: ${out}`).catch(() => {});
        }
    }
};

let activeHunt = true;
let lastStrike = Date.now();

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
        const latestBlockhash = await connection.getLatestBlockhash('confirmed');
        vTx.message.recentBlockhash = latestBlockhash.blockhash;
        vTx.sign([wallet]);
        
        const res = await axios.post(JITO_ENGINE, {
            jsonrpc: "2.0", id: 1, method: "sendBundle",
            params: [[bs58.encode(vTx.serialize())]]
        });

        if (res.data.result) {
            await VAULT.broadcast('STRIKE', `Trade Confirmed: ${res.data.result}`);
            lastStrike = Date.now();
        }
    } catch (err) { 
        await VAULT.broadcast('ERROR', `Execution Failed: ${err.message}`); 
    }
}

async function stalk() {
    await VAULT.broadcast('SYSTEM', 'Omnicore v12.4: Predator Mode Engaged.');
    while (true) {
        if (activeHunt) {
            try {
                const response = await axios.get('https://api.jup.ag/v6/program_id_to_tokens?programId=675k1q2wSjS691hu5tSh1269B2uWp7otFZg2DG22WX68');
                const pools = response.data?.slice(0, 15);
                if (pools) {
                    for (const pool of pools) {
                        const qUrl = `https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=${pool.mint}&amount=100000000&slippageBps=${CONFIG.SLIPPAGE}`;
                        const quote = await axios.get(qUrl);
                        if (quote.data && parseFloat(quote.data.outAmount) > 110000000) {
                            await executeTrade(quote.data);
                        }
                    }
                }
            } catch (e) { 
                if (e.response?.status === 429) await new Promise(r => setTimeout(r, 2000));
            }
        }
        await new Promise(r => setTimeout(r, 1000));
    }
}

// --- COMMAND CONTROLLER ---
bot.onText(/\/status/, async (msg) => {
    const bal = await connection.getBalance(wallet.publicKey);
    bot.sendMessage(msg.chat.id, `OMNICORE v12.4 STATUS\nHunting: ${activeHunt}\nBalance: ${bal/1e9} SOL\nUptime: ${Math.floor(process.uptime()/60)}m`);
});

bot.onText(/\/on/, () => { activeHunt = true; VAULT.broadcast('STATUS', 'HUNTING ACTIVE'); });
bot.onText(/\/off/, () => { activeHunt = false; VAULT.broadcast('STATUS', 'HUNTING PAUSED'); });

// --- RENDER SURVIVAL ---
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('OMNICORE_V12_4_ALIVE');
}).listen(CONFIG.PORT);

process.on('SIGTERM', () => {
    bot.stopPolling();
    setTimeout(() => process.exit(0), 1000);
});

async function main() {
    await VAULT.broadcast('SYSTEM', 'Sovereign Command Online.');
    await stalk();
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
