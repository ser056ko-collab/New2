# E:\SuperchainBot\main.py
import asyncio
import random
import time
import logging
from web3 import Web3
from config.config import load_wallets_and_proxies
from config.chains import CHAINS
from config.network_configs import NETWORK_CONFIGS
from modules.swap import initialize_web3, get_account_info
from networks.megaeth_testnet.bebop_swap import bebop_swap
from networks.megaeth_testnet.gte_swap import perform_swap

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    start_time = time.time()
    wallet_proxy_pairs = load_wallets_and_proxies()
    if not wallet_proxy_pairs:
        logger.error("No wallet-proxy pairs available. Exiting.")
        return

    logger.info(f"Loaded wallet-proxy pairs: {[(addr[:10] + '...', ':'.join(p.split(':')[:2])) for _, p, addr in wallet_proxy_pairs]}")
    logger.info("Supported chains:")
    for chain, info in CHAINS.items():
        logger.info(f"  {chain}: {info['rpc']}")

    private_key, proxy, address = wallet_proxy_pairs[0]
    proxy_display = ':'.join(proxy.split(':')[:2])
    logger.info(f"\nTesting operations for wallet {address[:10]}... with proxy {proxy_display}...")

    w3 = initialize_web3("megaeth_testnet", proxy=proxy)
    address, balance_eth, weth_balance, _ = get_account_info(w3, private_key)
    if balance_eth < 0.00015:
        logger.error(f"Insufficient ETH balance ({balance_eth}) for transactions")
        return

    operations = [
        ("Wrap", lambda: bebop_swap(private_key, chain_name="megaeth_testnet", operation="wrap", simulate=False)),
        ("Unwrap", lambda: bebop_swap(private_key, chain_name="megaeth_testnet", operation="unwrap", simulate=False) if weth_balance >= 0.0001 else None),
        ("Swap", lambda: perform_swap(private_key, chain_name="megaeth_testnet", simulate=False))
    ]
    random.shuffle(operations)
    num_operations = random.randint(1, 3)
    logger.info(f"Selected {num_operations} operations")

    for i, (op_name, op_func) in enumerate(operations[:num_operations]):
        if op_func is None:
            logger.info(f"Skipping {op_name}: insufficient WETH balance ({weth_balance})")
            continue
        logger.info(f"Executing {op_name}...")
        result = await op_func()
        logger.info(f"{op_name} result: {result}")
        pause = random.uniform(10, 30)
        logger.info(f"Pausing for {pause:.2f} seconds...")
        await asyncio.sleep(pause)
        w3 = initialize_web3("megaeth_testnet", proxy=proxy)
        address, balance_eth, weth_balance, _ = get_account_info(w3, private_key)

    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())