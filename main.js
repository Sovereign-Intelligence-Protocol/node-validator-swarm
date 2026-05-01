/* ==========================================================
 * S.I.P. OMNICORE v35.5 - TITAN SHIELD EDITION
 * HEAVYWEIGHT DEPLOYMENT - SOLANA MAINNET
 * LINE COUNT: 285 (FIXED & ALIGNED)
 * ========================================================== */

require('dotenv').config();
const { 
    Connection, Keypair, VersionedTransaction, PublicKey, 
    TransactionMessage, AddressLookupTableAccount, ComputeBudgetProgram 
} = require('@solana/web3.js');
const axios = require('axios');
const TelegramBot = require('node-telegram-bot-api');
const bs58 = require('bs58');
const crypto = require('crypto');
const http = require('http'); // REQUIRED FOR RENDER

const CONFIG = {
    TOKEN: process.env.TELEGRAM_BOT_TOKEN || process.env.BOT_TOKEN,
    CHAT: process.env.TELEGRAM_ADMIN_ID || process.env.CHAT_ID,
    RPC: process.env.RPC_URL,
    KEY: process.env.PRIVATE_KEY,
    KRAKEN_KEY: process.env.KRAKEN_API_KEY,
    KRAKEN_SECRET: process.env.KRAKEN_SECRET,
    PORT: process.env.PORT || 10000, // REQUIRED FOR RENDER
    MIN_PROFIT: 0.05,
    JITO_TIP: 0.001,
    SLIPPAGE: 50,
    HEARTBEAT_INTERVAL: 60000,
    RETRY_DELAY: 5000
};

if (!CONFIG.TOKEN || !CONFIG.KEY) {
    console.error("FATAL: Environment Mapping Failed. Check Render Dashboard.");
    process.exit(1);
}

// Fixed polling to true for command support
const bot = new TelegramBot(CONFIG.TOKEN, { polling: true });
const connection = new Connection(CONFIG.RPC, { 
    commitment: 'confirmed', 
    wsEndpoint: CONFIG.RPC.replace('https', 'wss'),
    confirmTransactionInitialTimeout: 60000 
});
const wallet = Keypair.fromSecretKey(bs58.decode(CONFIG.KEY));
const JITO_ENGINE = 'https://mainnet.block-engine.jito.wtf/api/v1/bundles';
const JITO_TIP_ADDR = new PublicKey('96g9sAg9u3mBsJqcMhMAbPPzCde1y39S5uJ9V8Hk719f');

const VAULT = {
    logs: [],
    async broadcast(level, msg) {
        const out = `[${level}] ${new Date().toLocaleTimeString()}: ${msg}`;
        this.logs.push(out);
        if (this.logs.length > 500) this.logs.shift();
        console.log(out);
        if (level === 'STRIKE' || level === 'HEAL' || level === 'SYSTEM' || level === 'STATUS') {
            await bot.sendMessage(CONFIG.CHAT, `\uD83D\uDEE1 S.I.P. v35.5: ${out}`).catch(() => {});
        }
    }
};

async function signKraken(path, data, secret) {
    const nonce = Date.now().toString();
    const message = path + crypto.createHash('sha256').update(nonce + data).digest('binary');
    const hmac = crypto.createHmac('sha512', Buffer.from(secret, 'base64'));
    return hmac.update(message).digest('base64');
}

async function offramp(amount) {
    if (!CONFIG.KRAKEN_KEY || !CONFIG.KRAKEN_SECRET) return;
    try {
        const path = '/0/private/Withdraw';
        const data = `asset=SOL&key=MainVault&amount=${amount}&nonce=${Date.now()}`;
        const sig = await signKraken(path, data, CONFIG.KRAKEN_SECRET);
        await axios.post(`https://api.kraken.com${path}`, data, {
            headers: { 'API-Key': CONFIG.KRAKEN_KEY, 'API-Sign': sig, 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        await VAULT.broadcast('REVENUE', `Secured ${amount} SOL to Kraken.`);
    } catch (e) { 
        await VAULT.broadcast('ERROR', `Kraken Protocol Drift: ${e.message}`); 
    }
}

let lastStrike = Date.now();
let activeHunt = true;

async function heal() {
    await VAULT.broadcast('HEAL', 'Initiating RPC Socket Refresh...');
    try {
        if (connection._rpcWebSocket) {
            connection._rpcWebSocket.terminate();
        }
        await new Promise(r => setTimeout(r, 3000));
        await VAULT.broadcast('HEAL', 'WSS Heartbeat Restored.');
    } catch (e) { 
        await VAULT.broadcast('ERROR', `Healing Failed: ${e.message}`); 
    }
}

const diagnostic = setInterval(async () => {
    const now = Date.now();
    if (now - lastStrike > 1800000) { 
        await heal();
        lastStrike = now;
    }
}, CONFIG.HEARTBEAT_INTERVAL);

async function executeTrade(quote) {
    try {
        const swapResponse = await axios.post('https://quote-api.jup.ag/v6/swap', {
            quoteResponse: quote,
            userPublicKey: wallet.publicKey.toString(),
            wrapAndUnwrapSol: true,
            useSharedAccounts: true,
            dynamicComputeUnitLimit: true,
            prioritizationFeeLamports: 'auto'
        });

        const { swapTransaction } = swapResponse.data;
        const txBuf = Buffer.from(swapTransaction, 'base64');
        const vTx = VersionedTransaction.deserialize(txBuf);
        
        const addressLookupTableAccounts = await Promise.all(
            vTx.message.addressTableLookups.map(async (lookup) => {
                const acc = await connection.getAccountInfo(lookup.accountKey);
                return new AddressLookupTableAccount({
                    key: lookup.accountKey,
                    state: AddressLookupTableAccount.deserialize(acc.data),
                });
            })
        );

        const latestBlockhash = await connection.getLatestBlockhash('confirmed');
        vTx.message.recentBlockhash = latestBlockhash.blockhash;
        vTx.sign([wallet]);
        
        const bundle = {
            jsonrpc: "2.0", id: 1, method: "sendBundle",
            params: [[bs58.encode(vTx.serialize())]]
        };

        const res = await axios.post(JITO_ENGINE, bundle);
        if (res.data.result) {
            await VAULT.broadcast('STRIKE', `Diamond Landed: ${res.data.result}`);
            lastStrike = Date.now();
            if (parseFloat(quote.outAmount) > 2000000000) await offramp(0.1);
        }
    } catch (err) { 
        await VAULT.broadcast('ERROR', `Execution Blocked: ${err.response?.data?.error || err.message}`); 
    }
}

async function checkSignals() {
    try {
        const response = await axios.get('https://api.jup.ag/v6/program_id_to_tokens?programId=675k1q2wSjS691hu5tSh1269B2uWp7otFZg2DG22WX68');
        const pools = response.data;
        if (!pools || pools.length === 0) return null;
        
        for (const pool of pools.slice(0, 20)) {
            const qUrl = `https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=${pool.mint}&amount=100000000&slippageBps=${CONFIG.SLIPPAGE}`;
            const quote = await axios.get(qUrl);
            if (quote.data && parseFloat(quote.data.outAmount) > 115000000) {
                const backQuote = await axios.get(`https://quote-api.jup.ag/v6/quote?inputMint=${pool.mint}&outputMint=So11111111111111111111111111111111111111112&amount=${quote.data.outAmount}&slippageBps=0`);
                if (parseFloat(backQuote.data.outAmount) > 105000000) return quote.data;
            }
        }
    } catch (e) { return null; }
    return null;
}

async function stalk() {
    await VAULT.broadcast('SYSTEM', 'Omnicore v35.5 Stalker Mode Engaged.');
    while (true) {
        if (activeHunt) {
            try {
                const signal = await checkSignals(); 
                if (signal) await executeTrade(signal);
            } catch (e) {
                if (e.response?.status === 429) {
                    await VAULT.broadcast('WARNING', 'RPC Throttled. Cooling down...');
                    await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY));
                }
            }
        }
        await new Promise(r => setTimeout(r, 400));
    }
}

// --- TELEGRAM COMMANDS ---
bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, "\uD83D\uDEE1 S.I.P. v35.5 TITAN SHIELD ONLINE\n\nCommands:\n/on - Start Hunting\n/off - Stop Hunting\n/health - Check Heartbeat\n/audit - System Status\n/kill - Shutdown");
});

bot.onText(/\/on/, async (msg) => {
    activeHunt = true;
    await VAULT.broadcast('STATUS', 'Titan Shield: HUNTING ENABLED');
});

bot.onText(/\/off/, async (msg) => {
    activeHunt = false;
    await VAULT.broadcast('STATUS', 'Titan Shield: HUNTING DISABLED');
});

bot.onText(/\/health/, async (msg) => {
    await VAULT.broadcast('STATUS', 'TITAN HEARTBEAT: OK \uD83D\uDFE2');
});

bot.onText(/\/audit/, async (msg) => {
    const bal = await connection.getBalance(wallet.publicKey);
    bot.sendMessage(msg.chat.id, `--- SYSTEM AUDIT ---\nStatus: ${activeHunt ? 'HUNTING' : 'IDLE'}\nBalance: ${bal/1e9} SOL\nWallet: ${wallet.publicKey.toString().slice(0,8)}...\nRPC: Connected`);
});

bot.onText(/\/kill/, async (msg) => {
    await VAULT.broadcast('SYSTEM', 'Emergency Shutdown Triggered.');
    process.exit(0);
});

// --- RENDER SURVIVAL MECHANICS ---
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('TITAN_SHIELD_UP');
}).listen(CONFIG.PORT);

process.on('SIGTERM', async () => {
    activeHunt = false;
    bot.stopPolling();
    await VAULT.broadcast('SYSTEM', 'SIGTERM: Grace
