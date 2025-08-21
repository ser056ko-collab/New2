# networks/megaeth_testnet/wrap.py
from web3 import Web3
from config.chains import CHAINS
from config.network_configs import NETWORK_CONFIGS
import logging
import random
import time

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
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

_web3_cache = {}

def initialize_web3(chain_name, proxy=None):
    if chain_name in _web3_cache:
        return _web3_cache[chain_name]
    start_time = time.time()
    chain = CHAINS.get(chain_name)
    if not chain:
        raise ValueError(f"Chain {chain_name} not supported")
    w3 = Web3(Web3.HTTPProvider(chain["rpc"]))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {chain_name} RPC")
    _web3_cache[chain_name] = w3
    logger.info(f"Web3 initialized for {chain_name} in {time.time() - start_time:.2f} seconds")
    return w3

def get_account_info(w3, wallet_private_key):
    account = w3.eth.account.from_key(wallet_private_key)
    address = account.address
    balance = w3.eth.get_balance(address)
    balance_eth = float(w3.from_wei(balance, 'ether'))
    nonce = w3.eth.get_transaction_count(address)
    weth_contract = w3.eth.contract(address=WETH_CONTRACT, abi=WETH_ABI)
    weth_balance_wei = weth_contract.functions.balanceOf(address).call()
    weth_balance = weth_balance_wei / 10**18
    return address, balance_eth, nonce, weth_balance

async def wrap_eth(wallet_private_key, chain_name="megaeth_testnet", simulate=True):
    try:
        w3 = initialize_web3(chain_name)
        address, balance_eth, nonce, weth_balance = get_account_info(w3, wallet_private_key)
        logger.info(f"Balance for {address}: {balance_eth} ETH, WETH: {weth_balance}")

        # Берем 5–15% от баланса ETH
        swap_percentage = random.uniform(
            NETWORK_CONFIGS[chain_name]["percentage_range"][0],
            NETWORK_CONFIGS[chain_name]["percentage_range"][1]
        ) / 100
        amount_eth = balance_eth * swap_percentage
        amount_eth = round(amount_eth, 8)
        if amount_eth < 0.00000001:
            amount_eth = 0.00000001
        logger.info(f"Selected {swap_percentage*100:.2f}% of ETH balance: {amount_eth} ETH")

        if balance_eth < amount_eth + 0.0001:  # Резерв для газа
            return {"status": "error", "message": f"Insufficient ETH balance ({balance_eth} ETH) for {address}"}

        weth_contract = w3.eth.contract(address=WETH_CONTRACT, abi=WETH_ABI)
        amount_wei = w3.to_wei(amount_eth, 'ether')
        tx = weth_contract.functions.deposit().build_transaction({
            'from': address,
            'value': amount_wei,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CHAINS[chain_name]["chain_id"]
        })

        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
        if simulate:
            logger.info(f"Simulated wrap for {address}: {signed_tx.hash.hex()}")
            return {"status": "success", "message": f"Wrap {amount_eth} ETH prepared for {address}, tx hash: {signed_tx.hash.hex()}"}
        else:
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt["status"] == 1:
                logger.info(f"Wrap successful: {tx_hash.hex()}")
                return {"status": "success", "message": f"Wrap {amount_eth} ETH successful for {address}, tx hash: {tx_hash.hex()}"}
            else:
                logger.error(f"Wrap failed: {tx_hash.hex()}")
                return {"status": "error", "message": f"Wrap failed: {tx_hash.hex()}"}
    except Exception as e:
        logger.error(f"Wrap failed: {str(e)}")
        return {"status": "error", "message": str(e)}