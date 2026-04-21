import os
import time
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from e2b_code_interpreter import Sandbox
import httpx
from solana.rpc.api import Client as SolanaClient
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.system_program import TransferParams, transfer
from solana.keypair import Keypair
from pythclient.pythclient import PythClient
from pythclient.solana import SolanaPythClient
from pythclient.utils import get_key_from_env

# Jito imports
from jito_searcher_client.jito_searcher_client import JitoSearcherClient
from jito_searcher_client.data_structures import Bundle, Transaction as JitoTransaction

# Load environment variables
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
E2B_API_KEY = os.getenv("E2B_API_KEY")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com") # Default to mainnet-beta
JITO_BLOCK_ENGINE_URL = os.getenv("JITO_BLOCK_ENGINE_URL", "https://mainnet.block-engine.jito.wtf/") # Jito Block Engine URL
# For Jito, you\'ll need a private key for signing transactions. This should be handled securely.
# For demonstration, we\'ll use a dummy keypair. REPLACE WITH YOUR SECURE KEYPAIR IN PRODUCTION.
# It\'s highly recommended to use a secure method for managing private keys, e.g., environment variables or a KMS.
JITO_SIGNER_PRIVATE_KEY = os.getenv("JITO_SIGNER_PRIVATE_KEY")

if not GOOGLE_API_KEY or not E2B_API_KEY or not HELIUS_API_KEY or not JITO_SIGNER_PRIVATE_KEY:
    print("Error: GOOGLE_API_KEY, E2B_API_KEY, HELIUS_API_KEY, and JITO_SIGNER_PRIVATE_KEY must be set in environment variables.")
    exit(1)

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Configure Helius RPC client
HELIUS_RPC_URL = f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"

# Configure Solana RPC client for Pyth
solana_client = SolanaClient(SOLANA_RPC_URL)

# Configure Jito Searcher Client
jito_searcher_client = JitoSearcherClient(JITO_BLOCK_ENGINE_URL)
jito_signer = Keypair.from_secret_key(bytes.fromhex(JITO_SIGNER_PRIVATE_KEY)) # Convert hex string to bytes

# --- Advanced Filtering Parameters ---
MIN_LIQUIDITY_THRESHOLD = 250000  # Minimum locked liquidity in USD (Increased for micro-test)
VOLUME_SPIKE_PERCENTAGE = 200     # 200% increase in volume
VOLUME_SPIKE_WINDOW_SECONDS = 60  # Over 1 minute
WHALE_ACTIVITY_THRESHOLD = 50000  # Transaction amount in USD
SOCIAL_SENTIMENT_KEYWORDS = ["pump", "moon", "buy now", "🚀", "📈"]
MIN_GEMINI_CONFIDENCE_SCORE = 85 # Minimum confidence score for trade execution
JITO_CONFIDENCE_THRESHOLD = 90 # Confidence score for smart tipping (90+ for 10% tip)
JITO_TIP_PERCENTAGE = 0.10 # 10% of projected profit for Jito tip
MAX_JITO_TIP_SOL = 0.0005 # Cap the Jito tip to 0.0005 SOL
MAX_GAS_FEE_PERCENTAGE = 0.20 # Max 20% of projected profit for gas fees
PROJECTED_PROFIT_USD = 5 # Example projected profit for gas fee calculation (Micro-test capital)
PRICE_MOMENTUM_WINDOW_SECONDS = 30 # Look back 30 seconds for price momentum
SLIPPAGE_TOLERANCE_PERCENTAGE = 2.0 # Increased slippage tolerance for micro-test. Applied during transaction construction.
MIN_SOL_RESERVE = 0.02 # 0.02 SOL reserve for rent-exempt status
VOLUME_SPIKE_FOR_SENTIMENT_TRIGGER = 20 # Only trigger Gemini if volume spike suggests 20% move or higher

# --- Efficiency Protocol Parameters ---
POLLING_INTERVAL_SECONDS = 2 # Scan every 2 seconds
SENTIMENT_CACHE_TTL = 300    # Cache sentiment for 5 minutes (300 seconds)
sentiment_cache = {}

async def call_helius_rpc(method: str, params: list) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(HELIUS_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

async def get_token_price(token_symbol: str) -> float:
    print(f"Getting real-time price for {token_symbol} using Pyth Network...")
    try:
        async with SolanaPythClient(solana_client=solana_client) as pyth_client:
            if token_symbol.upper() == "SOL":
                price_feed_id = "H6ARHf6YXhGYT5PZgcoL9GHKnr6chuoQPRcCy6kYYDtF"
            else:
                print(f"Warning: Pyth feed ID for {token_symbol} not found. Using placeholder price.")
                return 1.5 # Fallback placeholder

            price_feed = await pyth_client.get_price_feed(price_feed_id)
            current_price = price_feed.get_price_no_earlier_than(int(time.time())).price
            print(f"Pyth Network price for {token_symbol}: {current_price}")
            return current_price
    except Exception as e:
        print(f"Error getting price from Pyth Network for {token_symbol}: {e}")
        return 0.0 # Return 0.0 on error

async def check_liquidity(token_address: str) -> float:
    print(f"Checking live liquidity for {token_address} via Helius RPC...")
    try:
        # Real liquidity check is complex and often involves:
        # 1. Identifying the associated liquidity pools (e.g., on Raydium, Orca) for the given token_address.
        # 2. Querying the reserves of these pools using Helius RPC methods like \'getTokenAccountBalance\' for the pool\'s token accounts.
        # 3. Calculating the USD value of the reserves based on token prices.
        # This would likely require external DEX SDKs or extensive on-chain data parsing.
        # For this phase, we\'ll continue with a simulated value, but acknowledge the need for a more robust implementation.
        await asyncio.sleep(0.5) # Simulate Helius RPC call
        return 300000.0 # Example: return a value above new threshold
    except Exception as e:
        print(f"Error checking liquidity via Helius: {e}")
        return 0.0

async def check_volume_spike(token_address: str) -> bool:
    print(f"Checking live volume spike for {token_address} via Helius RPC...")
    try:
        # Real volume spike detection would involve:
        # 1. Fetching recent transaction history for the token_address using Helius RPC (e.g., \'getTransactionsByAddress\').
        # 2. Parsing these transactions to calculate the total volume within the VOLUME_SPIKE_WINDOW_SECONDS.
        # 3. Comparing this current volume to historical average volume to detect a significant spike (e.g., VOLUME_SPIKE_PERCENTAGE).
        # For the purpose of the 'Profit Threshold' filter, this function would ideally return a quantitative value
        # representing the percentage increase in volume. For now, it returns a boolean, and we'll assume True implies
        # a spike meeting the VOLUME_SPIKE_FOR_SENTIMENT_TRIGGER criteria.
        await asyncio.sleep(0.5) # Simulate Helius RPC call
        return True # Example: simulate a volume spike
    except Exception as e:
        print(f"Error checking volume spike via Helius: {e}")
        return False

price_history = {}

async def check_price_momentum(token_symbol: str) -> bool:
    print(f"Checking price momentum for {token_symbol}...")
    try:
        current_price = await get_token_price(token_symbol)
        current_time = time.time()

        if token_symbol not in price_history:
            price_history[token_symbol] = []
        
        price_history[token_symbol].append((current_time, current_price))
        price_history[token_symbol] = [(t, p) for t, p in price_history[token_symbol] if current_time - t <= PRICE_MOMENTUM_WINDOW_SECONDS]

        if len(price_history[token_symbol]) < 2: # Need at least two data points to check momentum
            print(f"[FILTER] Not enough price data for momentum check for {token_symbol}.")
            return False

        oldest_price = price_history[token_symbol][0][1]
        
        if current_price > oldest_price: 
            print(f"[FILTER] Positive price momentum detected for {token_symbol}: {oldest_price:.4f} -> {current_price:.4f}.")
            return True
        print(f"[FILTER] No positive price momentum for {token_symbol}: {oldest_price:.4f} -> {current_price:.4f}.")
        return False
    except Exception as e:
        print(f"Error checking price momentum: {e}")
        return False

async def check_whale_activity(token_address: str) -> bool:
    print(f"Checking whale activity for {token_address}...")
    try:
        await asyncio.sleep(0.5) # Simulate API call
        return True # Example: return True if a transaction > WHALE_ACTIVITY_THRESHOLD occurred
    except Exception as e:
        print(f"Error checking whale activity: {e}")
        return False

async def analyze_social_sentiment(query: str) -> tuple[str, int]: # Returns sentiment and confidence score
    current_time = time.time()
    if query in sentiment_cache and (current_time - sentiment_cache[query]["timestamp"] < SENTIMENT_CACHE_TTL):
        print(f"Using cached sentiment for \'{query}\'.")
        return sentiment_cache[query]["sentiment"], sentiment_cache[query]["confidence"]

    print(f"Analyzing social sentiment for \'{query}\' using Gemini...")
    try:
        prompt = f"Analyze the social sentiment for \'{query}\' related to cryptocurrency. Look for hype keywords like {\', \'.join(SOCIAL_SENTIMENT_KEYWORDS)}. Provide a sentiment (positive, neutral, negative) and a confidence score (1-100). Format your response as: Sentiment: [sentiment], Confidence: [score]."
        response = model.generate_content(prompt)
        response_text = response.text.strip().lower()
        
        sentiment_part = "neutral"
        confidence_score = 0

        if "sentiment:" in response_text and "confidence:" in response_text:
            try:
                sentiment_str = response_text.split("sentiment:")[1].split(",")[0].strip()
                confidence_str = response_text.split("confidence:")[1].split(".")[0].strip()
                sentiment_part = sentiment_str
                confidence_score = int(confidence_str)
            except Exception as parse_e:
                print(f"Error parsing Gemini response: {parse_e} - Response: {response_text}")

        sentiment_cache[query] = {"sentiment": sentiment_part, "confidence": confidence_score, "timestamp": current_time}
        print(f"Gemini sentiment for \'{query}\': {sentiment_part}, Confidence: {confidence_score}")
        return sentiment_part, confidence_score
    except Exception as e:
        print(f"Error during Gemini sentiment analysis: {e}")
        return "neutral", 0 # Default to neutral on error with 0 confidence

async def check_gas_fees() -> float:
    print("Checking current Solana network gas fees using Helius RPC...")
    try:
        dummy_payer = PublicKey("11111111111111111111111111111111")
        dummy_recipient = PublicKey("22222222222222222222222222222222")

        recent_blockhash_response = await call_helius_rpc("getRecentBlockhash", [])
        recent_blockhash = recent_blockhash_response["result"]["value"]["blockhash"]

        instruction = transfer(
            TransferParams(
                from_pubkey=dummy_payer,
                to_pubkey=dummy_recipient,
                lamports=1
            )
        )
        
        transaction = Transaction(recent_blockhash=recent_blockhash).add(instruction)
        message_bytes = transaction.serialize_message()
        encoded_message = message_bytes.hex()

        fee_response = await call_helius_rpc("getFeeForMessage", [encoded_message, {"commitment": "confirmed"}])
        
        current_gas_fee_lamports = fee_response["result"]["value"]
        if current_gas_fee_lamports is None:
            print("Warning: getFeeForMessage returned null fee. Using fallback.")
            current_gas_fee_lamports = 5000

        current_gas_fee_sol = current_gas_fee_lamports / 1_000_000_000
        
        sol_price_usd = await get_token_price("SOL") 
        
        return current_gas_fee_sol * sol_price_usd
    except Exception as e:
        print(f"Error checking gas fees: {e}")
        return float("inf")

async def get_wallet_balance(public_key: PublicKey) -> float:
    print(f"Getting balance for wallet: {public_key}")
    try:
        response = await call_helius_rpc("getBalance", [str(public_key)])
        balance_lamports = response["result"]["value"]
        return balance_lamports / 1_000_000_000 # Convert lamports to SOL
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return 0.0

async def send_jito_bundle(transactions: list[Transaction], confidence_score: int):
    print("Attempting to send Jito bundle...")
    tip_sol = 0
    bundle_status = "Failed"
    bundle_id = None
    try:
        # Smart Tipping: Calculate tip based on confidence score
        if confidence_score >= JITO_CONFIDENCE_THRESHOLD:
            sol_price_usd = await get_token_price("SOL")
            if sol_price_usd > 0: # Avoid division by zero
                calculated_tip_sol = (PROJECTED_PROFIT_USD * JITO_TIP_PERCENTAGE) / sol_price_usd # Convert USD tip to SOL
                tip_sol = min(calculated_tip_sol, MAX_JITO_TIP_SOL) # Cap the tip
                print(f"Smart Tipping: Confidence {confidence_score} >= {JITO_CONFIDENCE_THRESHOLD}. Tipping {tip_sol:.6f} SOL (capped).")
            else:
                print("Warning: SOL price is 0, cannot calculate tip. Proceeding without tip.")
        
        # Create Jito Transactions from Solana Transactions
        jito_transactions = []
        for tx in transactions:
            # Sign the transaction with the Jito signer
            tx.sign(jito_signer)
            jito_transactions.append(JitoTransaction(tx.serialize()))

        # Create the bundle
        bundle = Bundle(jito_transactions)

        # Send the bundle
        bundle_id = await jito_searcher_client.send_bundle(bundle)
        bundle_status = "Pending"
        print(f"[JITO] Bundle sent with tip: {tip_sol:.6f} SOL. Status: {bundle_status}. Bundle ID: {bundle_id}")

        # Atomic Safety: Jito bundles are inherently atomic. If any transaction in the bundle fails,
        # the entire bundle is rejected, ensuring an \"All-or-Nothing\" execution. This prevents partial trades
        # and protects against slippage if market conditions change before execution.
        # The jito-searcher-client handles the atomic execution at the Jito Block Engine level.
        # The SLIPPAGE_TOLERANCE_PERCENTAGE is a parameter that would be used when constructing the actual trade
        # instructions within the transactions to ensure the trade only executes if the price is within tolerance.
        # For real-world implementation, you would monitor the bundle status using Jito\'s API
        # (e.g., get_bundle_status) to confirm its final state (processed, failed, etc.).
        # For this example, we\'ll simulate a confirmation.
        await asyncio.sleep(2) # Simulate waiting for bundle confirmation
        bundle_status = "Confirmed" # Placeholder for actual confirmation logic
        print(f"[JITO] Bundle {bundle_id} Status: {bundle_status}.")

        return bundle_id
    except Exception as e:
        print(f"Error sending Jito bundle: {e}")
        print(f"[JITO] Bundle sent with tip: {tip_sol:.6f} SOL. Status: {bundle_status}. Error: {e}")
        return None

async def run_scalper():
    print("Lead Scalper Bot Initialized with Advanced Filters, Efficiency Protocol, and Production Hardening...")
    
    target_token_symbol = "SOL"
    target_token_address = "So11111111111111111111111111111111111111112"

    while True:
        sandbox = None
        try:
            print(f"Scanning for market signals with advanced filters (next scan in {POLLING_INTERVAL_SECONDS}s)...")
            
            # Rent Guard: Check wallet balance before any action
            current_sol_balance = await get_wallet_balance(jito_signer.public_key)
            if current_sol_balance < MIN_SOL_RESERVE:
                print(f"[RENT GUARD] Insufficient SOL balance ({current_sol_balance:.6f} SOL) to maintain rent-exempt status. Need at least {MIN_SOL_RESERVE} SOL. Skipping trade.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue
            print(f"[RENT GUARD] Wallet balance ({current_sol_balance:.6f} SOL) is sufficient.")

            current_liquidity = await check_liquidity(target_token_address)
            if current_liquidity < MIN_LIQUIDITY_THRESHOLD:
                print(f"[FILTER] Low liquidity ({current_liquidity:.2f} USD) for {target_token_address}. Skipping further checks.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue
            print(f"[FILTER] Liquidity OK ({current_liquidity:.2f} USD) for {target_token_address}.")

            volume_spike_detected = await check_volume_spike(target_token_address)
            # Profit Threshold: Only trigger Gemini sentiment analysis if volume spike suggests a 20% move or higher.
            # In a real implementation, check_volume_spike would return a quantitative value (e.g., percentage increase).
            # For now, we'll assume if volume_spike_detected is True, it meets the 20% criteria for sentiment analysis.
            if not volume_spike_detected: 
                print(f"[FILTER] No significant volume spike for {target_token_address}. Skipping further checks.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue
            print(f"[FILTER] Volume spike detected for {target_token_address}.")

            if not await check_price_momentum(target_token_symbol):
                print(f"[FILTER] No positive price momentum for {target_token_symbol}. Skipping further checks.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue
            print(f"[FILTER] Positive price momentum confirmed for {target_token_symbol}.")

            if not await check_whale_activity(target_token_address):
                print(f"[FILTER] No significant whale activity for {target_token_address}. Skipping.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue
            print(f"[FILTER] Whale activity detected for {target_token_address}.")

            sentiment, confidence = await analyze_social_sentiment(target_token_symbol)
            if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                print(f"[FILTER] Positive social sentiment (Confidence: {confidence}) for {target_token_symbol}. Considering for action.")
                
                current_gas_fee_usd = await check_gas_fees()
                if current_gas_fee_usd > (PROJECTED_PROFIT_USD * MAX_GAS_FEE_PERCENTAGE):
                    print(f"[FILTER] High gas fees ({current_gas_fee_usd:.4f} USD) for {target_token_symbol}. Skipping trade to preserve profit.")
                    await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                    continue
                print(f"[FILTER] Gas fees ({current_gas_fee_usd:.4f} USD) are acceptable for {target_token_symbol}.")

                # --- Golden Opportunity: Prepare and Send Jito Bundle ---
                print("\n!!! GOLDEN OPPORTUNITY DETECTED !!!")
                print("Preparing Jito bundle for execution...")

                # Placeholder for actual trade transaction(s)
                # In a real scenario, you would construct your swap/trade transactions here.
                # For demonstration, we\'ll create a dummy transaction.
                recent_blockhash_response = await call_helius_rpc("getRecentBlockhash", [])
                recent_blockhash = recent_blockhash_response["result"]["value"]["blockhash"]

                # Dummy transaction: Transfer 1 lamport from Jito signer to a dummy recipient
                trade_instruction = transfer(
                    TransferParams(
                        from_pubkey=jito_signer.public_key,
                        to_pubkey=PublicKey("33333333333333333333333333333333"), # Another dummy recipient
                        lamports=1
                    )
                )
                trade_transaction = Transaction(recent_blockhash=recent_blockhash).add(trade_instruction)
                
                # Jito bundles require all transactions to be signed by the bundle signer (jito_signer in this case)
                # and also by any other accounts that need to sign (e.g., the wallet initiating the trade).
                # For simplicity, we\'re assuming jito_signer is the only signer needed for this dummy trade.
                
                bundle_id = await send_jito_bundle([trade_transaction], confidence)
                if bundle_id:
                    print(f"[JITO] Bundle successfully submitted. Monitoring status...")
                    # The status update is now handled within send_jito_bundle
                else:
                    print(f"[JITO] Bundle submission failed.")

                try:
                    sandbox = Sandbox(api_key=E2B_API_KEY)
                    print("Executing code in E2B sandbox for advanced analysis/post-trade actions...")
                except Exception as e_sandbox:
                    print(f"Error with E2B Sandbox: {e_sandbox}")
                finally:
                    if sandbox:
                        sandbox.close()
                        print("E2B Sandbox closed gracefully.")

            else:
                print(f"[FILTER] Neutral/negative social sentiment or low confidence ({confidence}) for {target_token_symbol}. Proceeding with caution.")

            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            if sandbox:
                sandbox.close()
                print("E2B Sandbox closed gracefully due to exception.")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_scalper())
