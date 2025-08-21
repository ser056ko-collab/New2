# E:\SuperchainBot\modules\swap.py
from web3 import Web3
from config.chains import CHAINS
import logging
import time
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WETH_CONTRACT = Web3.to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19")

WETH_ABI = [
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