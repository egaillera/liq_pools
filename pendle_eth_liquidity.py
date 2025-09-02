import os
import sys
import requests
import math
from dotenv import load_dotenv

# --- Price Fetching ---

def get_usd_prices():
    """Fetches current USD prices for PENDLE and ETH from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {'ids': 'pendle,ethereum', 'vs_currencies': 'usd'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            'pendle_usd': data['pendle']['usd'],
            'eth_usd': data['ethereum']['usd']
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching USD prices from CoinGecko: {e}")
        return None

# --- Calculation ---

def calculate_liquidity(total_usd, min_price, max_price, current_price, usd_prices):
    """Calculates the required amounts of PENDLE and ETH."""
    if min_price >= max_price:
        print("Error: Minimum price must be less than maximum price.")
        return None, None

    sqrt_current = math.sqrt(current_price)
    sqrt_min = math.sqrt(min_price)
    sqrt_max = math.sqrt(max_price)
    
    pendle_usd = usd_prices['pendle_usd']
    eth_usd = usd_prices['eth_usd']

    if current_price <= min_price: # Position is all PENDLE
        amount_pendle = total_usd / pendle_usd
        amount_eth = 0
    elif current_price >= max_price: # Position is all ETH
        amount_pendle = 0
        amount_eth = total_usd / eth_usd
    else: # Position is mixed
        # With ETH/PENDLE price, ETH is token0 and PENDLE is token1
        denominator = ( ( (sqrt_max - sqrt_current) / (sqrt_current * sqrt_max) ) * eth_usd) + \
                      ( (sqrt_current - sqrt_min) * pendle_usd)
        
        if denominator == 0: return None, None
        
        liquidity = total_usd / denominator

        amount_eth = liquidity * ( (sqrt_max - sqrt_current) / (sqrt_current * sqrt_max) )
        amount_pendle = liquidity * (sqrt_current - sqrt_min)
        
    return amount_pendle, amount_eth


# --- Main Execution ---

def get_user_input(current_price):
    """Gets investment details from the user interactively."""
    while True:
        try:
            total_usd = float(input("Enter the total amount to invest in USD: "))
            if total_usd > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    while True:
        try:
            min_price = float(input(f"Enter the minimum price for the position (ETH per PENDLE) (current: {current_price:.8f}): "))
            if min_price > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    while True:
        try:
            max_price = float(input(f"Enter the maximum price for the position (ETH per PENDLE) (current: {current_price:.8f}): "))
            if max_price > min_price:
                break
            else:
                print("Maximum price must be greater than the minimum price.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    return total_usd, min_price, max_price

def main():
    print("--- Uniswap V3 Liquidity Calculator ---")
    print("This script helps you calculate the required tokens for a liquidity position.")
    print("-" * 25, "\n")

    print("Fetching prices from CoinGecko...")
    usd_prices = get_usd_prices()

    if not usd_prices:
        sys.exit(1)

    eth_pendle_price = usd_prices['eth_usd'] / usd_prices['pendle_usd']

    print(f"  - Current ETH/PENDLE Price: {eth_pendle_price:.8f}")
    print(f"  - Current PENDLE Price (USD): ${usd_prices['pendle_usd']:,.2f}")
    print(f"  - Current ETH Price (USD):  ${usd_prices['eth_usd']:,.2f}")
    print("-" * 25, "\n")

    total_usd, min_price, max_price = get_user_input(eth_pendle_price)

    amount_pendle, amount_eth = calculate_liquidity(total_usd, min_price, max_price, eth_pendle_price, usd_prices)

    if amount_pendle is not None:
        print("--- Required Liquidity ---")
        print(f"For a ${total_usd:,.2f} investment with a range of {min_price:.8f} to {max_price:.8f} ETH/PENDLE:\n")
        print(f"  You will need to supply:")
        print(f"    - {amount_pendle:.8f} PENDLE")
        print(f"    - {amount_eth:.8f} ETH\n")
        
        # Verification
        total_value = (amount_pendle * usd_prices['pendle_usd']) + (amount_eth * usd_prices['eth_usd'])
        print("Value verification:")
        print(f"  - PENDLE Value: ${amount_pendle * usd_prices['pendle_usd']:,.2f}")
        print(f"  - ETH Value:  ${amount_eth * usd_prices['eth_usd']:,.2f}")
        print(f"  - Total Calculated Value: ${total_value:,.2f}")

if __name__ == "__main__":
    main()
