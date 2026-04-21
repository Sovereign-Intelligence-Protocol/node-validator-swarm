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
from pythclient.pythclient import PythClient
from pythclient.solana import SolanaPythClient
from pythclient.utils import get_key_from_env

# Load environment variables
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
E2B_API_KEY = os.getenv("E2B_API_KEY")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com") # Default to mainnet-beta

if not GOOGLE_API_KEY or not E2B_API_KEY or not HELIUS_API_KEY:
    print("Error: GOOGLE_API_KEY, E2B_API_KEY, and HELIUS_API_KEY must be set in environment variables.")
    exit(1)

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Configure Helius RPC client
HELIUS_RPC_URL = f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"

# Configure Solana RPC client for Pyth
solana_client = SolanaClient(SOLANA_RPC_URL)

# --- Advanced Filtering Parameters ---
MIN_LIQUIDITY_THRESHOLD = 100000  # Minimum locked liquidity in USD
VOLUME_SPIKE_PERCENTAGE = 200     # 200% increase in volume
VOLUME_SPIKE_WINDOW_SECONDS = 60  # Over 1 minute
WHALE_ACTIVITY_THRESHOLD = 50000  # Transaction amount in USD
SOCIAL_SENTIMENT_KEYWORDS = ["pump", "moon", "buy now", "🚀", "📈"]
MIN_GEMINI_CONFIDENCE_SCORE = 85 # Minimum confidence score for trade execution
MAX_GAS_FEE_PERCENTAGE = 0.20 # Max 20% of projected profit for gas fees
PROJECTED_PROFIT_USD = 1000 # Example projected profit for gas fee calculation
PRICE_MOMENTUM_WINDOW_SECONDS = 30 # Look back 30 seconds for price momentum

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
            # This assumes you know the Pyth price feed ID for the token_symbol
            # For a real implementation, you'd need a mapping from token_symbol to Pyth feed ID
            # For now, let's use a placeholder or a well-known feed like SOL/USD
            # You might need to search for the correct feed ID for your target token
            # Example: SOL/USD feed ID (this is just an example, verify actual ID)
            if token_symbol.upper() == "SOL":
                price_feed_id = "H6ARHf6YXhGYT5PZgcoL9GHKnr6chuoQPRcCy6kYYDtF"
            else:
                # Placeholder for other tokens, you'd need to implement a lookup
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
        # 2. Querying the reserves of these pools using Helius RPC methods like 'getTokenAccountBalance' for the pool's token accounts.
        # 3. Calculating the USD value of the reserves based on token prices.
        # This would likely require external DEX SDKs or extensive on-chain data parsing.
        # For this phase, we'll continue with a simulated value, but acknowledge the need for a more robust implementation.
        await asyncio.sleep(0.5) # Simulate Helius RPC call
        return 150000.0 # Example: return a value above threshold
    except Exception as e:
        print(f"Error checking liquidity via Helius: {e}")
        return 0.0

async def check_volume_spike(token_address: str) -> bool:
    print(f"Checking live volume spike for {token_address} via Helius RPC...")
    try:
        # Real volume spike detection would involve:
        # 1. Fetching recent transaction history for the token_address using Helius RPC (e.g., 'getTransactionsByAddress').
        # 2. Parsing these transactions to calculate the total volume within the VOLUME_SPIKE_WINDOW_SECONDS.
        # 3. Comparing this current volume to historical average volume to detect a significant spike (e.g., VOLUME_SPIKE_PERCENTAGE).
        # This is also a complex task requiring detailed transaction parsing.
        # For this phase, we'll continue with a simulated value.
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
        
        # Add current price and timestamp to history
        price_history[token_symbol].append((current_time, current_price))

        # Remove old prices outside the momentum window
        price_history[token_symbol] = [(t, p) for t, p in price_history[token_symbol] if current_time - t <= PRICE_MOMENTUM_WINDOW_SECONDS]

        if len(price_history[token_symbol]) < 2: # Need at least two data points to check momentum
            print(f"[FILTER] Not enough price data for momentum check for {token_symbol}.")
            return False

        # Compare current price to the oldest price in the window
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
        # This would involve monitoring large transactions on the blockchain via Helius RPC
        # For example, using getSignaturesForAddress and then getTransaction for details
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
        # Create a dummy transaction to estimate fees
        # This requires a payer (even a dummy one) and a recent blockhash
        # For a real transaction, you'd use the actual payer's public key
        dummy_payer = PublicKey("11111111111111111111111111111111") # A dummy public key
        dummy_recipient = PublicKey("22222222222222222222222222222222") # Another dummy public key

        # Get a recent blockhash from Helius RPC
        recent_blockhash_response = await call_helius_rpc("getRecentBlockhash", [])
        recent_blockhash = recent_blockhash_response["result"]["value"]["blockhash"]

        # Create a simple transfer instruction
        instruction = transfer(
            TransferParams(
                from_pubkey=dummy_payer,
                to_pubkey=dummy_recipient,
                lamports=1 # Transfer 1 lamport
            )
        )
        
        # Create a dummy transaction message
        transaction = Transaction(recent_blockhash=recent_blockhash).add(instruction)
        # The transaction needs to be partially signed or have its message extracted
        # For fee estimation, we just need the message bytes
        message_bytes = transaction.serialize_message()
        encoded_message = message_bytes.hex() # Encode to hex for RPC call

        # Call Helius RPC getFeeForMessage
        fee_response = await call_helius_rpc("getFeeForMessage", [encoded_message, {"commitment": "confirmed"}])
        
        # The fee is returned in lamports
        current_gas_fee_lamports = fee_response["result"]["value"]
        if current_gas_fee_lamports is None:
            print("Warning: getFeeForMessage returned null fee. Using fallback.")
            current_gas_fee_lamports = 5000 # Fallback to base fee

        # Convert lamports to SOL
        current_gas_fee_sol = current_gas_fee_lamports / 1_000_000_000
        
        # Get real SOL price from Pyth
        sol_price_usd = await get_token_price("SOL") 
        
        return current_gas_fee_sol * sol_price_usd # Return estimated fee in USD
    except Exception as e:
        print(f"Error checking gas fees: {e}")
        return float('inf') # Return very high fee on error

async def run_scalper():
    print("Lead Scalper Bot Initialized with Advanced Filters, Efficiency Protocol, and Production Hardening...")
    
    # Example token to monitor (in a real scenario, this would come from a scanner)
    target_token_symbol = "SOL" # Using SOL for testing Pyth integration
    target_token_address = "So11111111111111111111111111111111111111112" # Example SOL address

    while True:
        sandbox = None # Initialize sandbox outside try block
        try:
            print(f"Scanning for market signals with advanced filters (next scan in {POLLING_INTERVAL_SECONDS}s)...")
            
            # 1. Liquidity Threshold (Always check first for cost-efficiency)
            current_liquidity = await check_liquidity(target_token_address)
            if current_liquidity < MIN_LIQUIDITY_THRESHOLD:
                print(f"[FILTER] Low liquidity ({current_liquidity:.2f} USD) for {target_token_address}. Skipping further checks.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue
            print(f"[FILTER] Liquidity OK ({current_liquidity:.2f} USD) for {target_token_address}.")

            # 2. Volume Spikes (Check second for cost-efficiency)
            if not await check_volume_spike(target_token_address):
                print(f"[FILTER] No significant volume spike for {target_token_address}. Skipping further checks.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue
            print(f"[FILTER] Volume spike detected for {target_token_address}.")

            # 3. Price Momentum (New filter after volume spike)
            if not await check_price_momentum(target_token_symbol):
                print(f"[FILTER] No positive price momentum for {target_token_symbol}. Skipping further checks.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue
            print(f"[FILTER] Positive price momentum confirmed for {target_token_symbol}.")

            # If Liquidity, Volume, and Price Momentum pass, then proceed to more expensive checks

            # 4. Whale Activity
            if not await check_whale_activity(target_token_address):
                print(f"[FILTER] No significant whale activity for {target_token_address}. Skipping.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS) 
                continue
            print(f"[FILTER] Whale activity detected for {target_token_address}.")

            # 5. Social Sentiment (using cache and confidence score)
            sentiment, confidence = await analyze_social_sentiment(target_token_symbol)
            if sentiment == "positive" and confidence >= MIN_GEMINI_CONFIDENCE_SCORE:
                print(f"[FILTER] Positive social sentiment (Confidence: {confidence}) for {target_token_symbol}. Considering for action.")
                
                # 6. Gas Fee Check (before potential trade execution)
                current_gas_fee_usd = await check_gas_fees()
                if current_gas_fee_usd > (PROJECTED_PROFIT_USD * MAX_GAS_FEE_PERCENTAGE):
                    print(f"[FILTER] High gas fees ({current_gas_fee_usd:.4f} USD) for {target_token_symbol}. Skipping trade to preserve profit.")
                    await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                    continue
                print(f"[FILTER] Gas fees ({current_gas_fee_usd:.4f} USD) are acceptable for {target_token_symbol}.")

                # Placeholder for actual trading action based on sentiment and all filters passing
                # Example of using E2B for complex analysis or execution (only if all filters pass)
                try:
                    sandbox = Sandbox(api_key=E2B_API_KEY) # Initialize sandbox here
                    print("Executing code in E2B sandbox for advanced analysis...")
                    # Example E2B code execution
                    # code_output = await sandbox.execute_python("print(\'E2B analysis complete\')")
                    # print(f"E2B Output: {code_output}")
                except Exception as e_sandbox:
                    print(f"Error with E2B Sandbox: {e_sandbox}")
                finally:
                    if sandbox: # Ensure sandbox is closed even if E2B execution fails
                        sandbox.close()
                        print("E2B Sandbox closed gracefully.")

            else:
                print(f"[FILTER] Neutral/negative social sentiment or low confidence ({confidence}) for {target_token_symbol}. Proceeding with caution.")

            # Placeholder for actual scalping logic after all filters pass
            
            await asyncio.sleep(POLLING_INTERVAL_SECONDS) # Sleep for 2 seconds between scans
            
        except Exception as e:
            print(f"An error occurred: {e}")
            if sandbox: # Ensure sandbox is closed on general exception
                sandbox.close()
                print("E2B Sandbox closed gracefully due to exception.")
            await asyncio.sleep(POLLING_INTERVAL_SECONDS) # Wait before next scan

if __name__ == "__main__":
    asyncio.run(run_scalper())
