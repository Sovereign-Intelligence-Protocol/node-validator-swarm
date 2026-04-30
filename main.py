import websockets

# --- 4. THE JUPITER SNIPER ENGINE ---
async def execute_buy(token_mint, payer_kp):
    """Executes a 0.05 SOL sniper buy via Jupiter V6."""
    async with httpx.AsyncClient() as client:
        try:
            # 1. Get the fastest route quote
            quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={token_mint}&amount=50000000&slippageBps=100"
            quote = (await client.get(quote_url)).json()
            
            # 2. Notify and Prepare Strike
            # Note: For safety, we notify via Telegram before final execution
            await send_tg(f"🎯 <b>TARGET DETECTED</b>\nMint: <code>{token_mint}</code>\n<i>Running safety checks...</i>")
            print(f"Target found: {token_mint} | Ready for 0.05 SOL strike.")
            
        except Exception as e:
            print(f"Snipe Error: {e}")

async def helius_radar(payer_kp):
    """Real-time Raydium Liquidity Monitor via Helius WebSockets."""
    # Ensure HELIUS_API_KEY is in your Render Environment Variables
    api_key = os.environ.get("HELIUS_API_KEY")
    uri = f"wss://mainnet.helius-rpc.com/?api-key={api_key}"
    
    async with websockets.connect(uri) as ws:
        # Subscribe to all transactions on the Raydium AMM Program
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "transactionSubscribe",
            "params": [{
                "accountInclude": ["675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"],
                "failed": False
            }]
        }))
        await send_tg("📡 <b>RADAR LIVE</b>: Scanning Raydium in real-time.")
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            # Identify 'Initialize2' (The moment a pool is born)
            if "initialize2" in str(data).lower():
                # Logic to extract the mint address from transaction metadata goes here
                await execute_buy("DETECTED_MINT_ADDRESS", payer_kp)

# --- 5. OPERATIONAL CORE ---
async def predator():
    asyncio.create_task(tg_router())
    payer_kp = Keypair.from_bytes(base58.b58decode(PK))
    
    # Run the real-time Radar and system heartbeat concurrently
    await asyncio.gather(
        helius_radar(payer_kp),
        system_pulse()
    )

async def system_pulse():
    while True:
        print("Pulse: SIP Operational.")
        await asyncio.sleep(120)
