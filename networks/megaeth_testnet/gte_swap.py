# E:\SuperchainBot\networks\megaeth_testnet\gte_swap.py
from web3 import Web3
from config.chains import CHAINS
from config.network_configs import NETWORK_CONFIGS
import logging
import random
import time
import asyncio
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GTE_SWAPS_CONTRACT = Web3.to_checksum_address("0xA6b579684E943F7D00d616A48cF99b5147fC57A5")
BALANCE_CHECKER_CONTRACT_ADDRESS = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
WETH_CONTRACT = Web3.to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19")

GTE_TOKENS = {
    "WETH": {"address": "0x776401b9BC8aAe31A685731B7147D4445fD9FB19", "decimals": 18},
    "GTE": {"address": "0x9629684df53db9E4484697D0A50C442B2BFa80A8", "decimals": 18},
    "USDC": {"address": "0x8d635c4702ba38b1f1735e8e784c7265dcc0b623", "decimals": 6},
    "tkUSDC": {"address": "0xfaf334e157175ff676911adcf0964d7f54f2c424", "decimals": 6},
    "MegaETH": {"address": "0x10a6be7d23989D00d528E68cF8051d095f741145", "decimals": 18},
    "Kimchizuki": {"address": "0xA626F15D10F2b30AF1fb0d017F20a579500B5029", "decimals": 18},
    "five": {"address": "0xF512886BC6877B0740E8Ca0B3c12bb4cA602B530", "decimals": 18},
    "gte pepe": {"address": "0xBBA08CF5ECE0cC21e1DEB5168746c001B123A756", "decimals": 18},
}

GTE_SWAPS_ABI = [...]  # Без изменений

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
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

BALANCE_CHECKER_ABI = [...]  # Без изменений

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
    nonce = w3.eth.get_transaction_count(address)
    balances = {}
    try:
        multicall_contract = w3.eth.contract(address=BALANCE_CHECKER_CONTRACT_ADDRESS, abi=BALANCE_CHECKER_ABI)
        token_addresses = ["0x0000000000000000000000000000000000000000"]
        token_addresses.extend([w3.to_checksum_address(token_data["address"]) for token_data in GTE_TOKENS.values()])
        users = [address]
        all_balances = multicall_contract.functions.balances(users, token_addresses).call()
        balances["native"] = float(w3.from_wei(all_balances[0], 'ether'))
        for i, token_symbol in enumerate(GTE_TOKENS.keys()):
            balances[token_symbol] = float(w3.from_wei(all_balances[i + 1], f"{'wei' if GTE_TOKENS[token_symbol]['decimals'] == 18 else 'mwei'}"))
    except Exception as e:
        logger.warning(f"Balance checker failed: {str(e)}. Using individual balance checks.")
        balances["native"] = balance_eth
        for token_symbol, token_data in GTE_TOKENS.items():
            token_contract = w3.eth.contract(address=w3.to_checksum_address(token_data["address"]), abi=ERC20_ABI)
            balance_wei = token_contract.functions.balanceOf(address).call()
            balances[token_symbol] = float(w3.from_wei(balance_wei, f"{'wei' if token_data['decimals'] == 18 else 'mwei'}"))
    return address, balance_eth, nonce, balances

async def calculate_min_output(w3, contract, path, amount_in, slippage_percentage=20):
    try:
        amounts = contract.functions.getAmountsOut(amount_in, path).call()
        expected_output = amounts[-1]
        min_output = expected_output * (100 - slippage_percentage) // 100
        logger.info(f"Expected output: {w3.from_wei(expected_output, 'ether' if path[-1] in [GTE_TOKENS[t]['address'] for t in GTE_TOKENS if GTE_TOKENS[t]['decimals'] == 18] else 'mwei')}, Min output after {slippage_percentage}% slippage: {w3.from_wei(min_output, 'ether' if path[-1] in [GTE_TOKENS[t]['address'] for t in GTE_TOKENS if GTE_TOKENS[t]['decimals'] == 18] else 'mwei')}")
        return min_output
    except Exception as e:
        logger.warning(f"Error calculating min output: {str(e)}. Using 0 as fallback.")
        return 0

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

async def perform_swap(wallet_private_key, chain_name="megaeth_testnet", simulate=True):
    try:
        w3 = initialize_web3(chain_name, proxy=None)
        address, balance_eth, nonce, balances = get_account_info(w3, wallet_private_key)
        logger.info(f"Balance for {address}: {balance_eth} ETH, {balances}")

        if balance_eth < 0.00015:
            return {"status": "error", "message": f"Insufficient ETH balance ({balance_eth} ETH) for {address}"}

        contract = w3.eth.contract(address=GTE_SWAPS_CONTRACT, abi=GTE_SWAPS_ABI)
        tokens_with_balance = {token: bal for token, bal in balances.items() if token != "native" and bal > 0}
        do_native_swap = random.choice([True, False])

        path = []
        swap_type = ""
        target_token = ""
        if not tokens_with_balance or do_native_swap:
            available_tokens = ["USDC", "GTE"]
            target_token = random.choice(available_tokens)
            path = [w3.to_checksum_address(GTE_TOKENS["WETH"]["address"]), w3.to_checksum_address(GTE_TOKENS[target_token]["address"])]
            swap_type = "native_token"
            logger.info(f"Created ETH -> {target_token} path: {path}, swap type: {swap_type}")
        else:
            source_token_symbol = random.choice(list(tokens_with_balance.keys()))
            source_token_address = w3.to_checksum_address(GTE_TOKENS[source_token_symbol]["address"])
            swap_to_eth = random.choice([True, False])
            if swap_to_eth:
                path = [source_token_address, w3.to_checksum_address(GTE_TOKENS["WETH"]["address"])]
                swap_type = "token_native"
                target_token = "ETH"
                logger.info(f"Created {source_token_symbol} -> ETH path: {path}, swap type: {swap_type}")
            else:
                available_targets = ["USDC", "GTE"]
                if available_targets:
                    target_token = random.choice(available_targets)
                    path = [source_token_address, w3.to_checksum_address(GTE_TOKENS[target_token]["address"])]
                    swap_type = "token_token"
                    logger.info(f"Created {source_token_symbol} -> {target_token} path: {path}, swap type: {swap_type}")
                else:
                    path = [source_token_address, w3.to_checksum_address(GTE_TOKENS["WETH"]["address"])]
                    swap_type = "token_native"
                    target_token = "ETH"
                    logger.info(f"Fallback: Created {source_token_symbol} -> ETH path: {path}, swap type: {swap_type}")

        if not path:
            return {"status": "error", "message": "Failed to generate valid swap path"}

        if swap_type == "native_token":
            swap_percentage = random.uniform(
                NETWORK_CONFIGS[chain_name]["percentage_range"][0],
                NETWORK_CONFIGS[chain_name]["percentage_range"][1]
            ) / 100
            amount_eth = int(balance_eth * swap_percentage * 10**18)
            amount_eth = min(amount_eth, int(balance_eth * 0.5 * 10**18))
            logger.info(f"Selected {swap_percentage*100:.2f}% of ETH balance: {w3.from_wei(amount_eth, 'ether')} ETH")
            if amount_eth < 10**10:
                return {"status": "error", "message": f"Amount too low: {w3.from_wei(amount_eth, 'ether')} ETH"}
            min_output = await calculate_min_output(w3, contract, path, amount_eth)
            deadline = int(time.time()) + 1200
            tx = contract.functions.swapExactETHForTokens(
                min_output, path, address, deadline
            ).build_transaction({
                "from": address,
                "value": amount_eth,
                "gas": 200000,
                "gasPrice": 1250,
                "nonce": nonce,
                "chainId": CHAINS[chain_name]["chain_id"]
            })
            if simulate:
                return {"status": "success", "message": f"Simulated swap {w3.from_wei(amount_eth, 'ether')} ETH to {target_token}"}
            receipt = await sign_and_send_transaction(w3, tx, wallet_private_key, f"Swap ETH -> {target_token}")
            return {"status": "success" if receipt and receipt["status"] == 1 else "error",
                    "message": f"Swap {w3.from_wei(amount_eth, 'ether')} ETH to {target_token} {'successful' if receipt and receipt['status'] == 1 else 'failed'}, tx hash: {receipt['transactionHash'].hex() if receipt else 'N/A'}"}

        elif swap_type == "token_native" or swap_type == "token_token":
            source_token_symbol = next(symbol for symbol, data in GTE_TOKENS.items() if data["address"].lower() == path[0].lower())
            decimals = GTE_TOKENS[source_token_symbol]["decimals"]
            amount_in = int(balances[source_token_symbol] * 0.5 * 10**decimals)
            if amount_in < 10**10:
                return {"status": "error", "message": f"Insufficient {source_token_symbol} balance: {balances[source_token_symbol]}"}
            logger.info(f"Selected 50% of {source_token_symbol} balance: {w3.from_wei(amount_in, 'ether' if decimals == 18 else 'mwei')} {source_token_symbol}")
            token_contract = w3.eth.contract(address=path[0], abi=ERC20_ABI)
            approval_tx = token_contract.functions.approve(GTE_SWAPS_CONTRACT, amount_in).build_transaction({
                "from": address,
                "gas": 100000,
                "gasPrice": 1250,
                "nonce": nonce,
                "chainId": CHAINS[chain_name]["chain_id"]
            })
            if simulate:
                return {"status": "success", "message": f"Simulated approval for {source_token_symbol}"}
            approval_receipt = await sign_and_send_transaction(w3, approval_tx, wallet_private_key, f"Approve {source_token_symbol}")
            if not approval_receipt or approval_receipt["status"] != 1:
                return {"status": "error", "message": f"Approval for {source_token_symbol} failed"}
            nonce += 1
            min_output = await calculate_min_output(w3, contract, path, amount_in)
            deadline = int(time.time()) + 1200
            if swap_type == "token_native":
                tx = contract.functions.swapExactTokensForETH(
                    amount_in, min_output, path, address, deadline
                ).build_transaction({
                    "from": address,
                    "gas": 250000,
                    "gasPrice": 1250,
                    "nonce": nonce,
                    "chainId": CHAINS[chain_name]["chain_id"]
                })
            else:
                tx = contract.functions.swapExactTokensForTokens(
                    amount_in, min_output, path, address, deadline
                ).build_transaction({
                    "from": address,
                    "gas": 250000,
                    "gasPrice": 1250,
                    "nonce": nonce,
                    "chainId": CHAINS[chain_name]["chain_id"]
                })
            if simulate:
                return {"status": "success", "message": f"Simulated swap {source_token_symbol} to {target_token}"}
            receipt = await sign_and_send_transaction(w3, tx, wallet_private_key, f"Swap {source_token_symbol} -> {target_token}")
            return {"status": "success" if receipt and receipt["status"] == 1 else "error",
                    "message": f"Swap {w3.from_wei(amount_in, 'ether' if decimals == 18 else 'mwei')} {source_token_symbol} to {target_token} {'successful' if receipt and receipt['status'] == 1 else 'failed'}, tx hash: {receipt['transactionHash'].hex() if receipt else 'N/A'}"}

    except Exception as e:
        logger.error(f"GTE swap failed: {str(e)}")
        return {"status": "error", "message": str(e)}