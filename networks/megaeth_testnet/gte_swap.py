# SuperchainBot\networks\megaeth_testnet\gte_swap.py
from web3 import Web3
from config.chains import CHAINS
from config.network_configs import NETWORK_CONFIGS
import logging
import random
import time
import asyncio
import requests
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GTE_SWAPS_CONTRACT = Web3.to_checksum_address("0xA6b579684E943F7D00d616A48cF99b5147fC57A5")
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

GTE_SWAPS_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

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

_web3_cache = {}

def initialize_web3(chain_name, proxy=None, simulate=False):
    if simulate:
        logger.info(f"Simulating Web3 initialization for {chain_name} via proxy {proxy.split(':')[0] + ':' + proxy.split(':')[1] if proxy else 'no proxy'}")
        class MockWeb3:
            class eth:
                chain_id = CHAINS[chain_name]["chain_id"]
                gas_price = 1250
                @staticmethod
                def contract(*args, **kwargs):
                    return MockContract()
                @staticmethod
                def get_balance(*args, **kwargs):
                    return int(random.uniform(0.01, 0.1) * 10**18)
                @staticmethod
                def get_transaction_count(*args, **kwargs):
                    return random.randint(0, 100)
                @staticmethod
                def estimate_gas(*args, **kwargs):
                    return 200000
                @staticmethod
                def send_raw_transaction(*args, **kwargs):
                    return bytes([0] * 32)
                @staticmethod
                def wait_for_transaction_receipt(*args, **kwargs):
                    return {"status": 1, "transactionHash": bytes([0] * 32)}
            def to_checksum_address(self, addr):
                return Web3.to_checksum_address(addr)
            def from_wei(self, value, unit):
                return Web3.from_wei(value, unit)
        class MockContract:
            class functions:
                @staticmethod
                def balanceOf(*args, **kwargs):
                    class Call:
                        def call(self):
                            return int(random.uniform(0.01, 0.1) * 10**18) if kwargs.get('args', [None])[0] != GTE_SWAPS_CONTRACT else int(random.uniform(10, 100) * 10**6)
                    return Call()
                @staticmethod
                def approve(*args):
                    class BuildTransaction:
                        def build_transaction(self, tx_params):
                            return tx_params
                    return BuildTransaction()
                @staticmethod
                def swapExactETHForTokens(*args):
                    class BuildTransaction:
                        def build_transaction(self, tx_params):
                            return tx_params
                    return BuildTransaction()
                @staticmethod
                def swapExactTokensForETH(*args):
                    class BuildTransaction:
                        def build_transaction(self, tx_params):
                            return tx_params
                    return BuildTransaction()
                @staticmethod
                def swapExactTokensForTokens(*args):
                    class BuildTransaction:
                        def build_transaction(self, tx_params):
                            return tx_params
                    return BuildTransaction()
                @staticmethod
                def getAmountsOut(*args):
                    class Call:
                        def call(self):
                            amount_in = args[0]
                            return [amount_in, int(amount_in * random.uniform(0.95, 1.05))]
                    return Call()
        return MockWeb3()
    
    cache_key = f"{chain_name}_{proxy or 'no_proxy'}"
    if cache_key in _web3_cache:
        return _web3_cache[cache_key]
    
    chain = CHAINS.get(chain_name)
    if not chain:
        raise ValueError(f"Chain {chain_name} not supported")
    
    if not proxy:
        raise ValueError(f"Proxy is required for {chain_name}")
    
    proxy_parts = proxy.split(':')
    if len(proxy_parts) != 4:
        raise ValueError("Invalid proxy format. Expected host:port:username:password")
    host, port, username, password = proxy_parts
    proxy_display = f"{host}:{port}"
    proxy_url = f'http://{username}:{password}@{host}:{port}'
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {'Proxy-Authorization': f'Basic {auth}'}
    
    rpc_urls = chain["rpc"] if isinstance(chain["rpc"], list) else [chain["rpc"]]
    
    for rpc_url in rpc_urls:
        for attempt in range(3):
            try:
                logger.info(f"Attempt {attempt + 1}/3 to connect to {rpc_url} via proxy {proxy_display}")
                # Проверка RPC через прокси
                response = requests.get(
                    rpc_url,
                    proxies={'http': proxy_url, 'https': proxy_url},
                    headers=headers,
                    timeout=15
                )
                if response.status_code != 200:
                    logger.warning(f"Proxy test failed for {rpc_url}: HTTP {response.status_code}")
                    continue
                provider = Web3.HTTPProvider(
                    rpc_url,
                    request_kwargs={
                        'proxies': {'http': proxy_url, 'https': proxy_url},
                        'headers': headers,
                        'timeout': 15
                    }
                )
                w3 = Web3(provider)
                if w3.is_connected():
                    _web3_cache[cache_key] = w3
                    logger.info(f"Web3 initialized for {chain_name} via {rpc_url} (proxy: {proxy_display})")
                    return w3
                else:
                    logger.warning(f"Web3 connection test failed for {rpc_url} via proxy {proxy_display}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error for {rpc_url} via proxy {proxy_display}: {str(e)}")
                if '407' in str(e):
                    logger.error(f"Proxy authentication failed for {proxy_display}. Check username and password.")
            except Exception as e:
                logger.warning(f"Error connecting to {rpc_url} via proxy {proxy_display} on attempt {attempt + 1}: {str(e)}")
                if attempt < 2:
                    pause = random.uniform(2, 5)
                    logger.info(f"Pausing for {pause:.2f} seconds before retry")
                    await asyncio.sleep(pause)
    
    raise ConnectionError(f"Failed to connect to {chain_name} RPC via proxy {proxy_display}. Tried URLs: {rpc_urls}")

def get_account_info(w3, address, simulate=False):
    try:
        balance = w3.eth.get_balance(address)
        balance_eth = float(w3.from_wei(balance, 'ether'))
        nonce = w3.eth.get_transaction_count(address)
        balances = {"native": balance_eth}
        for token_symbol, token_data in GTE_TOKENS.items():
            token_contract = w3.eth.contract(address=w3.to_checksum_address(token_data["address"]), abi=ERC20_ABI)
            balance_wei = token_contract.functions.balanceOf(address).call()
            balances[token_symbol] = float(w3.from_wei(balance_wei, f"{'ether' if token_data['decimals'] == 18 else 'mwei'}"))
        return balance_eth, nonce, balances
    except Exception as e:
        logger.error(f"Failed to get account info for {address[:10]}...: {str(e)}")
        raise

async def calculate_min_output(w3, contract, path, amount_in, slippage_percentage=20, simulate=False):
    if simulate:
        expected_output = amount_in * random.uniform(0.95, 1.05)
        min_output = expected_output * (100 - slippage_percentage) / 100
        unit = 'ether' if path[-1] in [GTE_TOKENS[t]['address'] for t in GTE_TOKENS if GTE_TOKENS[t]['decimals'] == 18] else 'mwei'
        logger.info(f"Simulated expected output: {w3.from_wei(int(expected_output), unit):.6f}, min output after {slippage_percentage}% slippage: {w3.from_wei(int(min_output), unit):.6f}")
        return int(min_output)
    try:
        amounts = contract.functions.getAmountsOut(amount_in, path).call()
        expected_output = amounts[-1]
        min_output = expected_output * (100 - slippage_percentage) // 100
        unit = 'ether' if path[-1] in [GTE_TOKENS[t]['address'] for t in GTE_TOKENS if GTE_TOKENS[t]['decimals'] == 18] else 'mwei'
        logger.info(f"Expected output: {w3.from_wei(expected_output, unit):.6f}, min output after {slippage_percentage}% slippage: {w3.from_wei(int(min_output), unit):.6f}")
        return min_output
    except Exception as e:
        logger.warning(f"Error calculating min output: {str(e)}. Using 0 as fallback.")
        return 0

async def sign_and_send_transaction(w3, tx, wallet_private_key, address, operation_name="transaction", simulate=False):
    if simulate:
        await asyncio.sleep(random.uniform(1, 5))
        tx_hash_hex = f"0x{'0'*64}"
        explorer_link = f"{CHAINS['megaeth_testnet']['explorer']}/{tx_hash_hex}"
        logger.info(f"Simulated {operation_name} for wallet {address[:10]}...: gas=200000, gasPrice=0.00125 Gwei")
        logger.info(f"{operation_name} sent (wallet {address[:10]}...): {explorer_link}")
        logger.info(f"{operation_name} successful (wallet {address[:10]}...): {explorer_link}")
        return {"status": 1, "transactionHash": tx_hash_hex}
    try:
        gas_estimate = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas_estimate * 1.2)
        tx["gasPrice"] = w3.eth.gas_price
        logger.info(f"Estimated gas for {operation_name} (wallet {address[:10]}...): {tx['gas']}, gasPrice: {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        explorer_link = f"{CHAINS['megaeth_testnet']['explorer']}/{tx_hash_hex}"
        logger.info(f"{operation_name} sent (wallet {address[:10]}...): {explorer_link}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt["status"] == 1:
            logger.info(f"{operation_name} successful (wallet {address[:10]}...): {explorer_link}")
            return receipt
        else:
            logger.error(f"{operation_name} failed (wallet {address[:10]}...): {explorer_link}")
            return None
    except Exception as e:
        logger.error(f"Error in {operation_name} (wallet {address[:10]}...): {str(e)}")
        return None

async def perform_swap(wallet_private_key, address, chain_name="megaeth_testnet", simulate=False, proxy=None):
    try:
        w3 = initialize_web3(chain_name, proxy, simulate)
        balance_eth, nonce, balances = get_account_info(w3, address, simulate)
        logger.info(f"Balance for wallet {address[:10]}...: {balance_eth:.6f} ETH, {balances}")

        gas_reserve = 0.0001
        if balance_eth < gas_reserve + 0.00015:
            return {"status": "error", "message": f"Insufficient ETH balance ({balance_eth:.6f} ETH) for wallet {address[:10]}..."}
        
        contract = w3.eth.contract(address=GTE_SWAPS_CONTRACT, abi=GTE_SWAPS_ABI)
        tokens_with_balance = {token: bal for token, bal in balances.items() if token != "native" and bal > 0}
        available_tokens = NETWORK_CONFIGS[chain_name].get("allowed_tokens", list(GTE_TOKENS.keys()))

        for i in range(random.randint(1, 3)):
            do_native_swap = random.choice([True, False])
            path = []
            swap_type = ""
            source_token_symbol = ""
            target_token_symbol = ""
            swap_percentage = random.uniform(0.01, 0.30)

            if do_native_swap or not tokens_with_balance:
                source_token_symbol = "ETH"
                target_token_symbol = random.choice([t for t in available_tokens if t != "WETH"])
                path = [w3.to_checksum_address(GTE_TOKENS["WETH"]["address"]), w3.to_checksum_address(GTE_TOKENS[target_token_symbol]["address"])]
                swap_type = "native_token"
                logger.info(f"Created {source_token_symbol} -> {target_token_symbol} path for wallet {address[:10]}...: {path}, swap type: {swap_type}")
            else:
                source_token_symbol = random.choice(list(tokens_with_balance.keys()))
                source_token_address = w3.to_checksum_address(GTE_TOKENS[source_token_symbol]["address"])
                swap_to_eth = random.choice([True, False])
                if swap_to_eth:
                    path = [source_token_address, w3.to_checksum_address(GTE_TOKENS["WETH"]["address"])]
                    swap_type = "token_native"
                    target_token_symbol = "ETH"
                    logger.info(f"Created {source_token_symbol} -> {target_token_symbol} path for wallet {address[:10]}...: {path}, swap type: {swap_type}")
                else:
                    target_token_symbol = random.choice([t for t in available_tokens if t != source_token_symbol])
                    path = [source_token_address, w3.to_checksum_address(GTE_TOKENS[target_token_symbol]["address"])]
                    swap_type = "token_token"
                    logger.info(f"Created {source_token_symbol} -> {target_token_symbol} path for wallet {address[:10]}...: {path}, swap type: {swap_type}")

            if not path:
                return {"status": "error", "message": f"Failed to generate valid swap path for wallet {address[:10]}..."}

            if swap_type == "native_token":
                amount_eth = int((balance_eth - gas_reserve) * swap_percentage * 10**18)
                amount_eth = min(amount_eth, int((balance_eth - gas_reserve) * 0.5 * 10**18))
                logger.info(f"Selected {swap_percentage*100:.2f}% of ETH balance: {w3.from_wei(amount_eth, 'ether'):.6f} ETH for wallet {address[:10]}...")
                if amount_eth < 10**10:
                    return {"status": "error", "message": f"Amount too low: {w3.from_wei(amount_eth, 'ether'):.6f} ETH for wallet {address[:10]}..."}
                min_output = await calculate_min_output(w3, contract, path, amount_eth, simulate=simulate)
                deadline = int(time.time()) + 1200
                tx = contract.functions.swapExactETHForTokens(
                    min_output, path, address, deadline
                ).build_transaction({
                    "from": address,
                    "value": amount_eth,
                    "gas": 200000,
                    "gasPrice": w3.eth.gas_price,
                    "nonce": nonce,
                    "chainId": CHAINS[chain_name]["chain_id"]
                })
                await asyncio.sleep(random.uniform(1, 5))
                receipt = await sign_and_send_transaction(w3, tx, wallet_private_key, address, f"Swap {source_token_symbol} -> {target_token_symbol}", simulate)
                result = {"status": "success" if receipt and receipt["status"] == 1 else "error",
                          "message": f"Swap {w3.from_wei(amount_eth, 'ether'):.6f} {source_token_symbol} to {target_token_symbol} {'successful' if receipt and receipt['status'] == 1 else 'failed'} for wallet {address[:10]}..., tx hash: {receipt['transactionHash'] if receipt else 'N/A'}"}
                logger.info(result["message"])
                if result["status"] == "success":
                    nonce += 1
                    balances = get_account_info(w3, address, simulate)[2]
                    tokens_with_balance = {token: bal for token, bal in balances.items() if token != "native" and bal > 0}

            elif swap_type == "token_native" or swap_type == "token_token":
                decimals = GTE_TOKENS[source_token_symbol]["decimals"]
                amount_in = int(balances[source_token_symbol] * swap_percentage * 10**decimals)
                amount_in = min(amount_in, int(balances[source_token_symbol] * 0.5 * 10**decimals))
                if amount_in < 10**10:
                    return {"status": "error", "message": f"Insufficient {source_token_symbol} balance: {balances[source_token_symbol]:.6f} for wallet {address[:10]}..."}
                logger.info(f"Selected {swap_percentage*100:.2f}% of {source_token_symbol} balance: {w3.from_wei(amount_in, 'ether' if decimals == 18 else 'mwei'):.6f} {source_token_symbol} for wallet {address[:10]}...")
                token_contract = w3.eth.contract(address=path[0], abi=ERC20_ABI)
                approval_tx = token_contract.functions.approve(GTE_SWAPS_CONTRACT, amount_in).build_transaction({
                    "from": address,
                    "gas": 100000,
                    "gasPrice": w3.eth.gas_price,
                    "nonce": nonce,
                    "chainId": CHAINS[chain_name]["chain_id"]
                })
                await asyncio.sleep(random.uniform(1, 5))
                approval_receipt = await sign_and_send_transaction(w3, approval_tx, wallet_private_key, address, f"Approve {source_token_symbol}", simulate)
                if not approval_receipt or approval_receipt["status"] != 1:
                    return {"status": "error", "message": f"Approval for {source_token_symbol} failed for wallet {address[:10]}..."}
                nonce += 1
                min_output = await calculate_min_output(w3, contract, path, amount_in, simulate=simulate)
                deadline = int(time.time()) + 1200
                if swap_type == "token_native":
                    tx = contract.functions.swapExactTokensForETH(
                        amount_in, min_output, path, address, deadline
                    ).build_transaction({
                        "from": address,
                        "gas": 250000,
                        "gasPrice": w3.eth.gas_price,
                        "nonce": nonce,
                        "chainId": CHAINS[chain_name]["chain_id"]
                    })
                else:
                    tx = contract.functions.swapExactTokensForTokens(
                        amount_in, min_output, path, address, deadline
                    ).build_transaction({
                        "from": address,
                        "gas": 250000,
                        "gasPrice": w3.eth.gas_price,
                        "nonce": nonce,
                        "chainId": CHAINS[chain_name]["chain_id"]
                    })
                await asyncio.sleep(random.uniform(1, 5))
                receipt = await sign_and_send_transaction(w3, tx, wallet_private_key, address, f"Swap {source_token_symbol} -> {target_token_symbol}", simulate)
                result = {"status": "success" if receipt and receipt["status"] == 1 else "error",
                          "message": f"Swap {w3.from_wei(amount_in, 'ether' if decimals == 18 else 'mwei'):.6f} {source_token_symbol} to {target_token_symbol} {'successful' if receipt and receipt['status'] == 1 else 'failed'} for wallet {address[:10]}..., tx hash: {receipt['transactionHash'] if receipt else 'N/A'}"}
                logger.info(result["message"])
                if result["status"] == "success":
                    nonce += 1
                    balances = get_account_info(w3, address, simulate)[2]
                    tokens_with_balance = {token: bal for token, bal in balances.items() if token != "native" and bal > 0}
            
            if i < random.randint(1, 3) - 1:
                pause = random.uniform(5, 30)
                logger.info(f"Pausing for {pause:.2f} seconds before next swap")
                await asyncio.sleep(pause)

        return {"status": "success", "message": f"Completed swaps for wallet {address[:10]}..."}

    except Exception as e:
        logger.error(f"GTE swap failed for wallet {address[:10]}...: {str(e)}")
        return {"status": "error", "message": str(e)}