# SuperchainBot\networks\megaeth_testnet\unwrap.py
from web3 import Web3
import logging
import random
import asyncio
from config.chains import CHAINS
from config.network_configs import NETWORK_CONFIGS
from .gte_swap import initialize_web3, get_account_info, sign_and_send_transaction

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WETH_CONTRACT = Web3.to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19")

WETH_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
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

async def unwrap_eth(wallet_private_key, address, chain_name="megaeth_testnet", simulate=False, proxy=None):
    try:
        w3 = initialize_web3(chain_name, proxy, simulate)
        balance_eth, nonce, _ = get_account_info(w3, address, simulate)
        weth_contract = w3.eth.contract(address=WETH_CONTRACT, abi=WETH_ABI)
        weth_balance = weth_contract.functions.balanceOf(address).call()
        weth_balance_eth = float(w3.from_wei(weth_balance, 'ether'))
        logger.info(f"Balance for wallet {address[:10]}...: {balance_eth:.6f} ETH, {weth_balance_eth:.6f} WETH")

        gas_reserve = 0.0001
        if balance_eth < gas_reserve:
            return {"status": "error", "message": f"Insufficient ETH balance ({balance_eth:.6f} ETH) for wallet {address[:10]}..."}

        if weth_balance_eth == 0:
            return {"status": "error", "message": f"No WETH balance for wallet {address[:10]}..."}

        swap_percentage = random.uniform(*NETWORK_CONFIGS[chain_name]["percentage_range"]) / 100
        amount_weth = int(weth_balance_eth * swap_percentage * 10**18)
        amount_weth = min(amount_weth, int(weth_balance_eth * 0.5 * 10**18))
        logger.info(f"Selected {swap_percentage*100:.2f}% of WETH balance: {w3.from_wei(amount_weth, 'ether'):.6f} WETH for wallet {address[:10]}...")

        if amount_weth < 10**10:
            return {"status": "error", "message": f"Amount too low: {w3.from_wei(amount_weth, 'ether'):.6f} WETH for wallet {address[:10]}..."}

        tx = weth_contract.functions.withdraw(amount_weth).build_transaction({
            "from": address,
            "gas": 100000,
            "gasPrice": w3.eth.gas_price if not simulate else 1250,
            "nonce": nonce,
            "chainId": CHAINS[chain_name]["chain_id"]
        })

        await asyncio.sleep(random.uniform(1, 5))
        receipt = await sign_and_send_transaction(w3, tx, wallet_private_key, address, "Unwrap WETH", simulate)
        if receipt and receipt["status"] == 1:
            return {"status": "success", "message": f"Unwrapped {w3.from_wei(amount_weth, 'ether'):.6f} WETH for wallet {address[:10]}..."}
        else:
            return {"status": "error", "message": f"Failed to unwrap {w3.from_wei(amount_weth, 'ether'):.6f} WETH for wallet {address[:10]}..."}
    except Exception as e:
        logger.error(f"Unwrap failed for wallet {address[:10]}...: {str(e)}")
        return {"status": "error", "message": str(e)}