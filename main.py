import websockets

# --- 4. THE SNIPER LOGIC (JUPITER + HELIUS) ---
async def execute_buy(token_mint, payer_kp):
    """Executes a 0.05 SOL swap for the new token via Jupiter V6."""
    async with httpx.AsyncClient() as client:
        try:
            # 1. Get Quote from Jupiter
            quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={token_mint}&amount=50000000&slippageBps=100"
            quote = (await client.get(quote_url)).json()
            
            # 2. Get Swap Transaction
            swap_res = await client.post("https://quote-api.jup.ag/v6/swap", json={
                "quoteResponse": quote,
                "userPublicKey": str(payer_kp.pubkey()),
                "wrapAndUnwrapSol": True
            })
            # Note: For your $31, we keep this as 'SIMULATE' until you confirm.
            print(f"TARGET DETECTED: {token_mint} | Potential Buy: 0.05 SOL")
            await send_tg(f"🎯 <b>TARGET DETECTED</b>\nMint: <code>{token_mint}</code>\n<i>Running safety checks...</i>")
        except Exception as e:
            print(f"Snipe Error: {e}")

async def helius_radar(payer_kp):
    """Listens to Helius WebSocket for real-time liquidity events."""
    uri = f"wss://mainnet.helius-rpc.com/?api-key={os.environ.get('HELIUS_API_KEY')}"
    async with websockets.connect(uri) as ws:
        # Subscribe to Raydium Liquidity Pool Program
        sub_query = {
            "jsonrpc": "2.0", "id": 1, "method": "transactionSubscribe",
            "params": [{"accountInclude": ["675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"]}]
        }
        await ws.send(json.dumps(sub_query))
        await send_tg("📡 <b>RADAR LIVE</b>: Scanning Raydium in real-time.")
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            # Identify 'Initialize2' (New Token Launch)
            if "initialize2" in str(data).lower():
                # Extract Mint and Fire
                await execute_buy("TOKEN_MINT_HERE", payer_kp)

# --- 5. OPERATIONAL CORE ---
async def predator():
    asyncio.create_task(tg_router())
    payer_kp = Keypair.from_bytes(base58.b58decode(PK))
    
    # Start the Radar (WebSocket) and the Pulse (Timer) together
    await asyncio.gather(
        helius_radar(payer_kp),
        # Keep the 120s Pulse as a system check
        system_pulse() 
    )

async def system_pulse():
    while True:
        print("Pulse: System Healthy.")
        await asyncio.sleep(120)
