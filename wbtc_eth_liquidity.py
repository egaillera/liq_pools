import os
import sys
import requests
import math
from dotenv import load_dotenv

# --- Price Fetching ---

def get_usd_prices():
    """Fetches current USD prices for WBTC and ETH from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {'ids': 'wrapped-bitcoin,ethereum', 'vs_currencies': 'usd'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            'wbtc_usd': data['wrapped-bitcoin']['usd'],
            'eth_usd': data['ethereum']['usd']
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching USD prices from CoinGecko: {e}")
        return None

# --- Calculation ---

def calculate_liquidity(total_usd, min_price_eth_per_wbtc, max_price_eth_per_wbtc, current_price_eth_per_wbtc, usd_prices):
    """Calculates the required amounts of WBTC and ETH."""
    if min_price_eth_per_wbtc >= max_price_eth_per_wbtc:
        print("Error: Minimum price must be less than maximum price.")
        return None, None

    # Invert prices to work with WBTC/ETH ratio for the formulas
    min_price = 1 / max_price_eth_per_wbtc
    max_price = 1 / min_price_eth_per_wbtc
    current_price = 1 / current_price_eth_per_wbtc

    sqrt_current = math.sqrt(current_price)
    sqrt_min = math.sqrt(min_price)
    sqrt_max = math.sqrt(max_price)
    
    wbtc_usd = usd_prices['wbtc_usd']
    eth_usd = usd_prices['eth_usd']

    if current_price <= min_price: # Position is all WBTC
        amount_wbtc = total_usd / wbtc_usd
        amount_eth = 0
    elif current_price >= max_price: # Position is all ETH
        amount_wbtc = 0
        amount_eth = total_usd / eth_usd
    else: # Position is mixed
        # With WBTC/ETH price, WBTC is token0 and ETH is token1
        denominator = ( ( (sqrt_max - sqrt_current) / (sqrt_current * sqrt_max) ) * wbtc_usd) + \
                      ( (sqrt_current - sqrt_min) * eth_usd)
        
        if denominator == 0: return None, None
        
        liquidity = total_usd / denominator

        amount_wbtc = liquidity * ( (sqrt_max - sqrt_current) / (sqrt_current * sqrt_max) )
        amount_eth = liquidity * (sqrt_current - sqrt_min)
        
    return amount_wbtc, amount_eth



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
            min_price = float(input(f"Enter the minimum price for the position (ETH per WBTC) (current: {current_price:.8f}): "))
            if min_price > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    while True:
        try:
            max_price = float(input(f"Enter the maximum price for the position (ETH per WBTC) (current: {current_price:.8f}): "))
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

    eth_wbtc_price = usd_prices['eth_usd'] / usd_prices['wbtc_usd']

    print(f"  - Current ETH/WBTC Price: {eth_wbtc_price:.8f}")
    print(f"  - Current WBTC Price (USD): ${usd_prices['wbtc_usd']:,.2f}")
    print(f"  - Current ETH Price (USD):  ${usd_prices['eth_usd']:,.2f}")
    print("-" * 25, "\n")

    total_usd, min_price, max_price = get_user_input(eth_wbtc_price)

    amount_wbtc, amount_eth = calculate_liquidity(total_usd, min_price, max_price, eth_wbtc_price, usd_prices)

    if amount_wbtc is not None:
        print("--- Required Liquidity ---")
        print(f"For a ${total_usd:,.2f} investment with a range of {min_price:.8f} to {max_price:.8f} ETH/WBTC:\n")
        print(f"  You will need to supply:")
        print(f"    - {amount_wbtc:.8f} WBTC")
        print(f"    - {amount_eth:.8f} ETH\n")
        
        # Verification
        total_value = (amount_wbtc * usd_prices['wbtc_usd']) + (amount_eth * usd_prices['eth_usd'])
        print("Value verification:")
        print(f"  - WBTC Value: ${amount_wbtc * usd_prices['wbtc_usd']:,.2f}")
        print(f"  - ETH Value:  ${amount_eth * usd_prices['eth_usd']:,.2f}")
        print(f"  - Total Calculated Value: ${total_value:,.2f}")

if __name__ == "__main__":
    main()
