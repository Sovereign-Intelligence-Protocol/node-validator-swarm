import os
import time
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from e2b_code_interpreter import Sandbox

# Load environment variables
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
E2B_API_KEY = os.getenv("E2B_API_KEY")

if not GOOGLE_API_KEY or not E2B_API_KEY:
    print("Error: GOOGLE_API_KEY and E2B_API_KEY must be set in environment variables.")
    exit(1)

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def run_scalper():
    print("Lead Scalper Bot Initialized...")
    
    # Example logic for the scalper
    while True:
        try:
            print("Scanning for market signals...")
            # Placeholder for actual scalping logic
            # chat = model.start_chat(history=[]) # This is inside main.py as required
            
            # Example of using E2B
            # with Sandbox(api_key=E2B_API_KEY) as sandbox:
            #     print("Executing code in E2B sandbox...")
            
            await asyncio.sleep(60) # Sleep for 60 seconds between scans
            
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_scalper())
