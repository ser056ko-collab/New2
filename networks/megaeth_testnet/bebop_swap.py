# E:\SuperchainBot\networks\megaeth_testnet\bebop_swap.py
from web3 import Web3
from config.chains import CHAINS
import logging
import random
import time
import asyncio
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WETH_CONTRACT = Web3.to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19")

WETH_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

_web3_cache = {}

def initialize_web3(chain_name, proxy=None):
    cache_key = f"{chain_name}_{proxy or 'no_proxy'}"
    if cache_key in _web3_cache:
        return _web3_cache[cache_key]
    start_time = time.time()
    chain = CHAINS.get(chain_name)
    if not chain:
        raise ValueError(f"Chain {chain_name} not supported")
    
    proxy_display = proxy
    if proxy:
        try:
            proxy_parts = proxy.split(':')
            host, port = proxy_parts[:2]
            proxy_url = f'http://{host}:{port}'
            proxy_display = f'{host}:{port}'
            provider = Web3.HTTPProvider(
                chain["rpc"],
                request_kwargs={'proxies': {'http': proxy_url, 'https': proxy_url}}
            )
        except ValueError as e:
            logger.error(f"Failed to parse proxy: {e}. Expected host:port")
            raise
    else:
        provider = Web3.HTTPProvider(chain["rpc"])
    
    w3 = Web3(provider)
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {chain_name} RPC via proxy {proxy_display or 'no proxy'}")
    _web3_cache[cache_key] = w3
    logger.info(f"Web3 initialized for {chain_name} via proxy {proxy_display or 'no proxy'} in {time.time() - start_time:.2f} seconds")
    return w3

def get_account_info(w3, wallet_private_key):
    account = w3.eth.account.from_key(wallet_private_key)
    address = account.address
    balance = w3.eth.get_balance(address)
    balance_eth = float(w3.from_wei(balance, 'ether'))
    weth_contract = w3.eth.contract(address=WETH_CONTRACT, abi=WETH_ABI)
    weth_balance = weth_contract.functions.balanceOf(address).call()
    balance_weth = float(w3.from_wei(weth_balance, 'ether'))
    nonce = w3.eth.get_transaction_count(address)
    return address, balance_eth, weth_balance, nonce

async def sign_and_send_transaction(w3, tx, wallet_private_key, operation_name="transaction"):
    try:
        gas_estimate = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas_estimate * 1.2)
        tx["gasPrice"] = 1250  # 0.00125 Gwei
        logger.info(f"Estimated gas for {operation_name}: {tx['gas']}, gasPrice: {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        explorer_link = f"{CHAINS['megaeth_testnet']['explorer']}/{tx_hash_hex}"
        logger.info(f"{operation_name} sent: {explorer_link}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt["status"] == 1:
            logger.info(f"{operation_name} successful: {explorer_link}")
            return receipt
        else:
            logger.error(f"{operation_name} failed: {explorer_link}")
            return None
    except Exception as e:
        logger.error(f"Error in {operation_name}: {str(e)}")
        return None

async def bebop_swap(wallet_private_key, chain_name="megaeth_testnet", operation="wrap", simulate=True):
    try:
        w3 = initialize_web3(chain_name, proxy=None)
        address, balance_eth, balance_weth, nonce = get_account_info(w3, wallet_private_key)
        logger.info(f"Balance for {address}: {balance_eth} ETH, {balance_weth} WETH")

        weth_contract = w3.eth.contract(address=WETH_CONTRACT, abi=WETH_ABI)

        if operation == "wrap":
            if balance_eth < 0.00015:
                return {"status": "error", "message": f"Insufficient ETH balance ({balance_eth} ETH) for {address}"}
            swap_percentage = random.uniform(0.05, 0.15)
            amount_eth = int(balance_eth * swap_percentage * 10**18)
            amount_eth = min(amount_eth, int(balance_eth * 0.5 * 10**18))  # Max 50%
            logger.info(f"Selected {swap_percentage*100:.2f}% of ETH balance: {w3.from_wei(amount_eth, 'ether')} ETH")
            if amount_eth < 10**10:
                return {"status": "error", "message": f"Amount too low: {w3.from_wei(amount_eth, 'ether')} ETH"}
            tx = weth_contract.functions.deposit().build_transaction({
                "from": address,
                "value": amount_eth,
                "gas": 100000,
                "gasPrice": 1250,
                "nonce": nonce,
                "chainId": CHAINS[chain_name]["chain_id"]
            })
            if simulate:
                return {"status": "success", "message": f"Simulated wrap {w3.from_wei(amount_eth, 'ether')} ETH for {address}"}
            receipt = await sign_and_send_transaction(w3, tx, wallet_private_key, f"Wrap ETH -> WETH")
            return {"status": "success" if receipt and receipt["status"] == 1 else "error",
                    "message": f"Wrap {w3.from_wei(amount_eth, 'ether')} ETH {'successful' if receipt and receipt['status'] == 1 else 'failed'} for {address}, tx hash: {receipt['transactionHash'].hex() if receipt else 'N/A'}"}

        elif operation == "unwrap":
            if balance_weth < 0.0001:
                return {"status": "error", "message": f"Insufficient WETH balance ({balance_weth} WETH) for {address}"}
            swap_percentage = random.uniform(0.05, 0.15)
            amount_weth = int(balance_weth * swap_percentage * 10**18)
            amount_weth = min(amount_weth, int(balance_weth * 0.5 * 10