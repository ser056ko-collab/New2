# SuperchainBot\config\network_configs.py
NETWORK_CONFIGS = {
    "megaeth_testnet": {
        "operations": [
            {"name": "wrap", "module": "networks.megaeth_testnet.wrap", "function": "wrap_eth"},
            {"name": "unwrap", "module": "networks.megaeth_testnet.unwrap", "function": "unwrap_eth"},
            {"name": "gte_swap", "module": "networks.megaeth_testnet.gte_swap", "function": "perform_swap"},
        ],
        "percentage_range": [1, 30],
        "pause_range": [5, 30],
        "min_operations": 1,
        "max_operations": 3,
        "allowed_tokens": ["WETH", "GTE", "USDC", "tkUSDC", "MegaETH", "Kimchizuki", "five", "gte pepe"]
    },
}