# modules/swap.py
from web3 import Web3
from config.network_configs import get_web3_instance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Swap:
    def __init__(self, network_name: str, private_key: str, proxy: str = None):
        self.network_name = network_name
        self.web3 = get_web3_instance(network_name)
        self.account = self.web3.eth.account.from_key(private_key)
        self.proxy = proxy

    def execute_swap(self, protocol: str, token_in: str, token_out: str, amount: int):
        logger.info(f"Swapping {amount} {token_in} to {token_out} via {protocol} on {self.network_name}")
        if protocol == "bebop":
            from networks.megaeth_testnet.bebop_swap import BebopSwap
            swapper = BebopSwap(self.web3, self.account, self.proxy)
            return swapper.swap(token_in, token_out, amount)
        elif protocol == "gte":
            from networks.megaeth_testnet.gte_swap import GTESwap
            swapper = GTESwap(self.web3, self.account, self.proxy)
            return swapper.swap(token_in, token_out, amount)
        else:
            raise ValueError(f"Protocol {protocol} not supported")