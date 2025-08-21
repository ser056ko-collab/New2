# modules/bridge.py
from web3 import Web3
from config.chains import CHAINS
from config.settings import SETTINGS
import logging
import time
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_web3(chain_name, proxy=None):
    start_time = time.time()
    chain = CHAINS.get(chain_name)
    if not chain:
        raise ValueError(f"Chain {chain_name} not supported")
    w3 = Web3(Web3.HTTPProvider(chain["rpc"]))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {chain_name} RPC")
    logger.info(f"Web3 initialized for {chain_name} in {time.time() - start_time:.2f} seconds")
    return w3

def get_account_info(w3, wallet_private_key):
    account = w3.eth.account.from_key(wallet_private_key)
    address = account.address
    balance = w3.eth.get_balance(address)
    balance_eth = float(w3.from_wei(balance, 'ether'))
    nonce = w3.eth.get_transaction_count(address)
    return address, balance_eth, nonce

async def perform_bridge(wallet_private_key, chain_name="megaeth_testnet"):
    start_time = time.time()
    try:
        w3 = initialize_web3(chain_name)
        address, balance_eth, nonce = get_account_info(w3, wallet_private_key)
        logger.info(f"Balance for {address} on {chain_name}: {balance_eth} ETH")

        if balance_eth < 0.0001:
            return {"status": "error", "message": f"Insufficient ETH balance ({balance_eth} ETH) for {address}"}

        bridge_percentage = random.uniform(
            SETTINGS["BALANCE_PERCENTAGE_TO_SWAP"][0],
            SETTINGS["BALANCE_PERCENTAGE_TO_SWAP"][1]
        ) / 100
        amount_in = balance_eth * bridge_percentage
        amount_in_wei = w3.to_wei(amount_in, 'ether')

        bridge_address = w3.to_checksum_address("0x000000000000000000000000000000000000dead")
        tx = {
            'from': address,
            'to': bridge_address,
            'value': amount_in_wei,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CHAINS[chain_name]["chain_id"]
        }

        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
        logger.info(f"Simulated bridge for {address}: {signed_tx.hash.hex()}")
        logger.info(f"Bridge simulation completed in {time.time() - start_time:.2f} seconds")
        return {"status": "success", "message": f"Bridge prepared for {address}, amount: {amount_in} ETH, tx hash: {signed_tx.hash.hex()}"}
    except Exception as e:
        logger.error(f"Bridge failed: {str(e)}")
        return {"status": "error", "message": str(e)}