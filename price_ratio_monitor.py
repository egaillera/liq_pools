
import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv, set_key

load_dotenv()

# --- Environment Variables ---
# Get the Arbitrum RPC URL from an environment variable
ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
# Get Telegram Bot Token and Chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # @ETHBTCPriceMonitorBot
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Telegram Configuration ---
def configure_telegram():
    """Checks for Telegram credentials and prompts the user if they are not found."""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not found.")
        if not TELEGRAM_BOT_TOKEN:
            bot_token = input("Please enter your Telegram Bot Token: ")
            set_key(".env", "TELEGRAM_BOT_TOKEN", bot_token)
            TELEGRAM_BOT_TOKEN = bot_token
        if not TELEGRAM_CHAT_ID:
            chat_id = input("Please enter your Telegram Chat ID: ")
            set_key(".env", "TELEGRAM_CHAT_ID", chat_id)
            TELEGRAM_CHAT_ID = chat_id
        print("Telegram credentials saved to .env file.")

# --- Instructions for Telegram Setup ---
# To get your TELEGRAM_BOT_TOKEN: Talk to the BotFather on Telegram.
# To get your TELEGRAM_CHAT_ID for @egaillera:
# 1. Search for the user @egaillera on Telegram and start a chat.
# 2. Forward a message from @egaillera to a bot like @userinfobot.
# 3. The bot will reply with the user's information, including the Chat ID.

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))

# Check if connected to the network
if not w3.is_connected():
    print("Error: Could not connect to the Arbitrum network.")
    exit()

# --- Uniswap V3 Contracts ---
# Uniswap V3 Factory address on Arbitrum
FACTORY_ADDRESS = w3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")

# Minimal ABI for the Uniswap V3 Factory
FACTORY_ABI = json.loads('''
[
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "tokenA",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "tokenB",
        "type": "address"
      },
      {
        "internalType": "uint24",
        "name": "fee",
        "type": "uint24"
      }
    ],
    "name": "getPool",
    "outputs": [
      {
        "internalType": "address",
        "name": "pool",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]
''')

# Minimal ABI for the Uniswap V3 Pool
POOL_ABI = json.loads('''
[
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {
                "internalType": "uint160",
                "name": "sqrtPriceX96",
                "type": "uint160"
            },
            {
                "internalType": "int24",
                "name": "tick",
                "type": "int24"
            },
            {
                "internalType": "uint16",
                "name": "observationIndex",
                "type": "uint16"
            },
            {
                "internalType": "uint16",
                "name": "observationCardinality",
                "type": "uint16"
            },
            {
                "internalType": "uint16",
                "name": "observationCardinalityNext",
                "type": "uint16"
            },
            {
                "internalType": "uint8",
                "name": "feeProtocol",
                "type": "uint8"
            },
            {
                "internalType": "bool",
                "name": "unlocked",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
''')

# Create a contract instance for the Factory
factory_contract = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)

# --- Token Information ---
# Token addresses on Arbitrum
WETH_ADDRESS = w3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
WBTC_ADDRESS = w3.to_checksum_address("0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f")
USDC_ADDRESS = w3.to_checksum_address("0xaf88d065e77c8cC2239327C5EDb3A432268e5831")

# Token decimals
WETH_DECIMALS = 18
WBTC_DECIMALS = 8
USDC_DECIMALS = 6

# --- Functions ---
def get_pool_address(tokenA, tokenB, fee):
    return factory_contract.functions.getPool(tokenA, tokenB, fee).call()

def get_pool_price(pool_address):
    pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)
    slot0 = pool_contract.functions.slot0().call()
    return slot0[0]

def calculate_price(sqrt_price_x96, decimals0, decimals1):
    return ((sqrt_price_x96 / 2**96)**2) * (10**(decimals0 - decimals1))

def send_telegram_notification(message):
    """Sends a message to a Telegram user or group."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token or chat ID not set. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram notification: {e}")

def main():
    configure_telegram()
    # --- Get ETH price in USDC ---
    # Fee for WETH/USDC pool is typically 0.05% (500)
    weth_usdc_pool_address = get_pool_address(WETH_ADDRESS, USDC_ADDRESS, 500)
    if weth_usdc_pool_address == "0x0000000000000000000000000000000000000000":
        print("WETH/USDC pool not found for fee 500. Trying 3000.")
        weth_usdc_pool_address = get_pool_address(WETH_ADDRESS, USDC_ADDRESS, 3000)
        if weth_usdc_pool_address == "0x0000000000000000000000000000000000000000":
            print("WETH/USDC pool not found for fee 3000 either.")
            return

    sqrt_price_x96 = get_pool_price(weth_usdc_pool_address)
    token0 = WETH_ADDRESS if WETH_ADDRESS < USDC_ADDRESS else USDC_ADDRESS
    token1 = USDC_ADDRESS if WETH_ADDRESS < USDC_ADDRESS else WETH_ADDRESS

    if token0 == WETH_ADDRESS: # Price is USDC per WETH
        eth_price = calculate_price(sqrt_price_x96, WETH_DECIMALS, USDC_DECIMALS)
    else: # Price is WETH per USDC, so we need to invert
        eth_price = 1 / calculate_price(sqrt_price_x96, USDC_DECIMALS, WETH_DECIMALS)

    print(f"The current price of ETH is: ${eth_price:,.2f}")

    # --- Get WBTC price in WETH ---
    # Fee for WBTC/WETH pool is typically 0.05% (500)
    wbtc_weth_pool_address = get_pool_address(WBTC_ADDRESS, WETH_ADDRESS, 500)
    if wbtc_weth_pool_address == "0x0000000000000000000000000000000000000000":
        print("WBTC/WETH pool not found for fee 500. Trying 3000.")
        wbtc_weth_pool_address = get_pool_address(WBTC_ADDRESS, WETH_ADDRESS, 3000)
        if wbtc_weth_pool_address == "0x0000000000000000000000000000000000000000":
            print("WBTC/WETH pool not found for fee 3000 either.")
            return

    sqrt_price_x96 = get_pool_price(wbtc_weth_pool_address)
    token0 = WBTC_ADDRESS if WBTC_ADDRESS < WETH_ADDRESS else WETH_ADDRESS
    token1 = WETH_ADDRESS if WBTC_ADDRESS < WETH_ADDRESS else WBTC_ADDRESS

    if token0 == WBTC_ADDRESS: # Price is WETH per WBTC
        wbtc_eth_ratio = calculate_price(sqrt_price_x96, WBTC_DECIMALS, WETH_DECIMALS)
    else: # Price is WBTC per WETH, so we need to invert
        wbtc_eth_ratio = 1 / calculate_price(sqrt_price_x96, WETH_DECIMALS, WBTC_DECIMALS)

    wbtc_price = wbtc_eth_ratio * eth_price
    print(f"The current price of WBTC is: ${wbtc_price:,.2f}")

    # --- Calculate and Check ETH/WBTC Ratio ---
    if wbtc_eth_ratio > 0:
        eth_wbtc_ratio = 1 / wbtc_eth_ratio
        print(f"The ETH/WBTC ratio is: {eth_wbtc_ratio:.8f}")

        # Read thresholds from JSON file
        try:
            with open("thresholds.json", "r") as f:
                thresholds = json.load(f)
            upper_percentage = thresholds.get("upper_percentage", 0)
            lower_percentage = thresholds.get("lower_percentage", 0)

            # Read thresholds from JSON file
            upper_threshold = thresholds.get("upper_threshold")
            lower_threshold = thresholds.get("lower_threshold")

            if upper_threshold is None or lower_threshold is None:
                print("Thresholds not found in thresholds.json. Skipping threshold check.")
                return

            print(f"Monitoring ETH/WBTC ratio against thresholds: {lower_threshold:.8f} - {upper_threshold:.8f})")

            # Check if ratio is outside thresholds
            if eth_wbtc_ratio > upper_threshold:
                message = f"📈 ETH/WBTC ratio is above the upper threshold!\n\nCurrent Ratio: {eth_wbtc_ratio:.8f}\nUpper Threshold: {upper_threshold:.8f}"
                send_telegram_notification(message)
            elif eth_wbtc_ratio < lower_threshold:
                message = f"📉 ETH/WBTC ratio is below the lower threshold!\n\nCurrent Ratio: {eth_wbtc_ratio:.8f}\nLower Threshold: {lower_threshold:.8f}"
                send_telegram_notification(message)

        except FileNotFoundError:
            print("thresholds.json not found. Skipping threshold check.")
        except json.JSONDecodeError:
            print("Error decoding thresholds.json. Skipping threshold check.")

if __name__ == "__main__":
    main()
