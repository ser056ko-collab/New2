# SuperchainBot\config\config.py
import os
from web3 import Web3

def load_wallets():
    wallets = []
    wallet_file = os.path.join(os.path.dirname(__file__), "..", "data", "wallets.txt")
    if not os.path.exists(wallet_file):
        raise FileNotFoundError(f"Wallets file not found: {wallet_file}")
    w3 = Web3()
    with open(wallet_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                if ":" in line:
                    private_key, address = line.split(":")
                else:
                    private_key = line
                    try:
                        account = w3.eth.account.from_key(private_key)
                        address = account.address
                    except Exception as e:
                        print(f"Invalid private key {private_key[:10]}...: {str(e)}")
                        continue
                wallets.append({"private_key": private_key, "address": address})
    if not wallets:
        raise ValueError("No valid wallets found in wallets.txt")
    return wallets

def load_proxies():
    proxies = []
    proxy_file = os.path.join(os.path.dirname(__file__), "..", "data", "proxies.txt")
    if os.path.exists(proxy_file):
        with open(proxy_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    proxies.append(line)
    return proxies

WALLETS = load_wallets()
PROXIES = load_proxies()