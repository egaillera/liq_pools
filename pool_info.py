#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script provides detailed information about a Uniswap V3 liquidity pool
on the Arbitrum network, based on the NFT Position ID.

Usage:
  1. Set your Arbitrum node provider URL as an environment variable:
     export ETHEREUM_NODE_URL="https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"

  2. Run the script with the NFT ID as the argument:
     python pool_info.py <YOUR_NFT_ID>
"""
import os
import sys
import argparse
from web3 import Web3
import json
from dotenv import load_dotenv

load_dotenv()
from dotenv import load_dotenv

load_dotenv()

# --- Contract Addresses and ABIs (These are the same for Mainnet and Arbitrum) ---

# Uniswap V3 Nonfungible Position Manager
NFPM_ADDRESS = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
NFPM_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH9","type":"address"},{"internalType":"address","name":"_tokenDescriptor_","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"approved","type":"address"},{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],"name":"ApprovalForAll","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Collect","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":false,"internalType":"uint128","name":"liquidity","type":"uint128"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"DecreaseLiquidity","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":false,"internalType":"uint128","name":"liquidity","type":"uint128"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"IncreaseLiquidity","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"WETH9","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"token0","type":"address"},{"internalType":"address","name":"token1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint256","name":"amount0Desired","type":"uint256"},{"internalType":"uint256","name":"amount1Desired","type":"uint256"},{"internalType":"uint256","name":"amount0Min","type":"uint256"},{"internalType":"uint256","name":"amount1Min","type":"uint256"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct INonfungiblePositionManager.MintParams","name":"params","type":"tuple"}],"name":"mint","outputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"positions","outputs":[{"internalType":"uint96","name":"nonce","type":"uint96"},{"internalType":"address","name":"operator","type":"address"},{"internalType":"address","name":"token0","type":"address"},{"internalType":"address","name":"token1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"feeGrowthInside0LastX128","type":"uint256"},{"internalType":"uint256","name":"feeGrowthInside1LastX128","type":"uint256"},{"internalType":"uint128","name":"tokensOwed0","type":"uint128"},{"internalType":"uint128","name":"tokensOwed1","type":"uint128"}],"stateMutability":"view","type":"function"}]')

# Uniswap V3 Factory
FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
FACTORY_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"_feeTo","type":"address"},{"internalType":"address","name":"_feeToSetter","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":true,"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"FeeAmountEnabled","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"oldOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnerChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":true,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":false,"internalType":"int24","name":"tickSpacing","type":"int24"},{"indexed":false,"internalType":"address","name":"pool","type":"address"}],"name":"PoolCreated","type":"event"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"pool","type":"address"}],"stateMutability":"view","type":"function"}]')

# Standard ERC20 ABI (for symbol and decimals)
ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"}]')

# Uniswap V3 Pool ABI (for slot0)
POOL_ABI = json.loads('[{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]')

# List of public RPC nodes for Arbitrum
PUBLIC_ARBITRUM_NODES = [
    "https://arb1.arbitrum.io/rpc",
    "https://rpc.ankr.com/arbitrum",
    "https://arbitrum-one.public.blastapi.io",
]

def tick_to_price(tick, decimals0, decimals1):
    """Converts a Uniswap V3 tick to a human-readable price."""
    return (1.0001 ** tick) * (10 ** (decimals0 - decimals1))

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Get Uniswap V3 pool info from an NFT ID on Arbitrum.")
    parser.add_argument("nft_id", type=int, help="The ID of the NFT representing the liquidity position.")
    args = parser.parse_args()

    # --- Initial Setup ---
    node_url = os.environ.get("ETHEREUM_NODE_URL")
    w3 = None

    # Try connecting with the provided node_url first
    if node_url:
        print(f"Attempting to connect using ETHEREUM_NODE_URL: {node_url}")
        try:
            w3_test = Web3(Web3.HTTPProvider(node_url))
            if w3_test.is_connected():
                w3 = w3_test
                print("Successfully connected using ETHEREUM_NODE_URL.")
            else:
                print(f"Warning: Could not connect to the node at {node_url}.")
        except Exception as e:
            print(f"Warning: An error occurred while connecting to {node_url}: {e}")

    # If the connection via ETHEREUM_NODE_URL failed or it wasn't set, try public nodes
    if not w3:
        if node_url:
             print("Falling back to public Arbitrum nodes...")
        else:
             print("ETHEREUM_NODE_URL not set. Trying public Arbitrum nodes...")
        
        print("Note: Public nodes may be slow or unreliable. For best results, set ETHEREUM_NODE_URL.")
        for url in PUBLIC_ARBITRUM_NODES:
            try:
                print(f"  Trying {url}... ", end="")
                w3_test = Web3(Web3.HTTPProvider(url))
                if w3_test.is_connected():
                    print("Success!")
                    w3 = w3_test
                    break
                else:
                    print("Failed.")
            except Exception:
                print("Failed.")

    # If still no connection, exit
    if not w3:
        print("\nError: Could not connect to any public Arbitrum nodes.")
        print("Please set the ETHEREUM_NODE_URL environment variable to a reliable Arbitrum node URL.")
        print("e.g., export ETHEREUM_NODE_URL='https://arbitrum-mainnet.infura.io/v3/YOUR_PROJECT_ID'")
        sys.exit(1)


    print("--- Uniswap V4 Notice ---")
    print("Uniswap V4 is not yet deployed.")
    print("This script retrieves information for Uniswap V3 pools on the Arbitrum Network.")
    print("-" * 25, "\n")


    try:
        nft_id = args.nft_id
        print(f"Fetching data for NFT Position ID: {nft_id} on Arbitrum...")

        # --- Contract Instances ---
        nfpm_contract = w3.eth.contract(address=NFPM_ADDRESS, abi=NFPM_ABI)
        factory_contract = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)

        # 1. Get Position Details from the NFT
        position = nfpm_contract.functions.positions(nft_id).call()
        token0_addr = position[2]
        token1_addr = position[3]
        fee = position[4]
        tick_lower = position[5]
        tick_upper = position[6]
        liquidity = position[7]

        # 2. Get Token Information
        token0_contract = w3.eth.contract(address=token0_addr, abi=ERC20_ABI)
        token1_contract = w3.eth.contract(address=token1_addr, abi=ERC20_ABI)

        token0_symbol = token0_contract.functions.symbol().call()
        token0_decimals = token0_contract.functions.decimals().call()
        token1_symbol = token1_contract.functions.symbol().call()
        token1_decimals = token1_contract.functions.decimals().call()

        # 3. Get Pool Address
        pool_address = factory_contract.functions.getPool(token0_addr, token1_addr, fee).call()

        # 4. Get Current Pool Price
        pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)
        slot0 = pool_contract.functions.slot0().call()
        current_tick = slot0[1]

        # --- Calculations ---
        # The price of token1 in terms of token0
        price_t1_in_t0 = tick_to_price(current_tick, token0_decimals, token1_decimals)
        price_lower = tick_to_price(tick_lower, token0_decimals, token1_decimals)
        price_upper = tick_to_price(tick_upper, token0_decimals, token1_decimals)

        # The price of token0 in terms of token1
        price_t0_in_t1 = 1 / price_t1_in_t0
        price_lower_inv = 1 / price_upper
        price_upper_inv = 1 / price_lower


        # --- Display Information ---
        print("\n--- Pool Information ---")
        print(f"Pool Address: {pool_address}")
        print(f"Tokens: {token0_symbol} / {token1_symbol}")
        print(f"Fee Tier: {fee / 10000}%")

        print("\n--- Current Market Price ---")
        print(f"1 {token1_symbol} = {price_t1_in_t0:.6f} {token0_symbol}")
        print(f"1 {token0_symbol} = {price_t0_in_t1:.6f} {token1_symbol}")
        print(f"Current Tick: {current_tick}")

        print("\n--- Your Position Details ---")
        print(f"Liquidity: {liquidity}")
        print(f"Status: {'In Range' if tick_lower <= current_tick <= tick_upper else 'Out of Range'}")

        print("\n--- Position Price Range ---")
        print("Range (Token1 in terms of Token0):")
        print(f"  Lower: 1 {token1_symbol} = {price_lower:.6f} {token0_symbol} (Tick: {tick_lower})")
        print(f"  Upper: 1 {token1_symbol} = {price_upper:.6f} {token0_symbol} (Tick: {tick_upper})")

        print("\nRange (Token0 in terms of Token1):")
        print(f"  Lower: 1 {token0_symbol} = {price_lower_inv:.6f} {token1_symbol}")
        print(f"  Upper: 1 {token0_symbol} = {price_upper_inv:.6f} {token1_symbol}")


    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check the following:")
        print("1. The NFT ID is correct and exists on the Arbitrum Network.")
        print("2. Your ETHEREUM_NODE_URL is a valid Arbitrum node URL and has access.")
        sys.exit(1)

if __name__ == "__main__":
    main()
