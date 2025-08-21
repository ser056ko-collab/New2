# SuperchainBot\main.py
import logging
import random
import asyncio
import importlib
from config.chains import CHAINS
from config.config import WALLETS, PROXIES
from config.network_configs import NETWORK_CONFIGS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def execute_operation(wallet, chain_name, operation, simulate=False, proxy=None):
    module_path = operation["module"]
    function_name = operation["function"]
    try:
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        logger.info(f"Executing {operation['name']} for wallet {wallet['address'][:10]}... on {chain_name} (simulate={simulate})")
        result = await func(wallet["private_key"], wallet["address"], chain_name, simulate, proxy)
        logger.info(f"Result of {operation['name']} for wallet {wallet['address'][:10]}...: {result}")
        return result
    except Exception as e:
        logger.warning(f"Operation {operation['name']} failed for wallet {wallet['address'][:10]}...: {str(e)}")
        return {"status": "error", "message": str(e)}

async def process_wallet(wallet, chain_name, simulate=False):
    operations = NETWORK_CONFIGS[chain_name]["operations"]
    min_ops = NETWORK_CONFIGS[chain_name]["min_operations"]
    max_ops = NETWORK_CONFIGS[chain_name]["max_operations"]
    pause_range = NETWORK_CONFIGS[chain_name]["pause_range"]
    proxy = random.choice(PROXIES) if PROXIES else None

    num_operations = random.randint(min_ops, max_ops)
    selected_operations = random.sample(operations, k=num_operations)
    
    for i, op in enumerate(selected_operations):
        result = await execute_operation(wallet, chain_name, op, simulate, proxy)
        if result["status"] == "error":
            logger.warning(f"Operation {op['name']} failed for wallet {wallet['address'][:10]}...: {result['message']}")
        if i < len(selected_operations) - 1:
            pause = random.uniform(pause_range[0], pause_range[1])
            logger.info(f"Pausing for {pause:.2f} seconds before next operation")
            await asyncio.sleep(pause)

async def main():
    for idx, wallet in enumerate(WALLETS, 1):
        logger.info(f"Processing wallet {idx}/{len(WALLETS)}: {wallet['address'][:10]}...")
        for chain_name in NETWORK_CONFIGS.keys():
            await process_wallet(wallet, chain_name, simulate=False)
            if idx < len(WALLETS):
                pause = random.uniform(10, 60)
                logger.info(f"Pausing for {pause:.2f} seconds before next wallet")
                await asyncio.sleep(pause)

if __name__ == "__main__":
    asyncio.run(main())