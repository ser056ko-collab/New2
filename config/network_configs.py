# config/network_configs.py
NETWORK_CONFIGS = {
    "megaeth_testnet": {
        "operations": [
            {"name": "wrap", "module": "networks.megaeth_testnet.wrap", "function": "wrap_eth"},
            {"name": "unwrap", "module": "networks.megaeth_testnet.unwrap", "function": "unwrap_eth"},
            {"name": "gte_swap", "module": "networks.megaeth_testnet.gte_swap", "function": "gte_swap"},
        ],
        "percentage_range": [5, 15],  # Проценты для операций
        "pause_range": [10, 30],  # Задержки в секундах
        "min_operations": 1,
        "max_operations": 3
    },
    # Добавь другие сети, например:
    # "goerli": {
    #     "operations": [...],
    #     "percentage_range": [5, 15],
    #     "pause_range": [10, 30],
    #     "min_operations": 1,
    #     "max_operations": 3
    # }
}