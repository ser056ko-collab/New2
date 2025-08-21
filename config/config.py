# E:\SuperchainBot\config\config.py
import os
import logging
from web3 import Web3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_wallets_and_proxies():
    wallets_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wallets.txt')
    proxies_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'proxies.txt')
    wallet_proxy_pairs = []

    try:
        with open(wallets_file, 'r', encoding='utf-8') as wf:
            wallets = [line.strip() for line in wf if line.strip()]

        with open(proxies_file, 'r', encoding='utf-8') as pf:
            proxies = [line.strip() for line in pf if line.strip()]

        for i in range(min(len(wallets), len(proxies))):
            private_key = wallets[i]
            proxy = proxies[i]
            if private_key and proxy:
                try:
                    w3 = Web3()
                    account = w3.eth.account.from_key(private_key)
                    address = account.address
                    proxy_display = proxy.split(':')[:2]  # Берем только host:port
                    proxy_display = ':'.join(proxy_display)
                    wallet_proxy_pairs.append((private_key, proxy, address))
                    logger.info(f"Loaded pair: wallet={address[:10]}..., proxy={proxy_display}")
                except Exception as e:
                    logger.warning(f"Skipping line {i+1}: Invalid private key, error={str(e)}")
            else:
                logger.warning(f"Skipping line {i+1}: wallet={'empty' if not private_key else 'valid'}, proxy={'empty' if not proxy else proxy}")

        if not wallet_proxy_pairs:
            logger.error("No valid wallet-proxy pairs found")
        return wallet_proxy_pairs

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading wallets/proxies: {e}")
        return []