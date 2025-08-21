# config/settings.py
SETTINGS = {
    "THREADS": 1,
    "ATTEMPTS": 1,  # Уменьшено до 1 попытки
    "SHUFFLE_WALLETS": True,
    "PAUSE_BETWEEN_SWAPS": [5, 30],  # Реалистичные задержки
    "SWAPS_AMOUNT": [1, 5],  # 1–5 повторений
    "BALANCE_PERCENTAGE_TO_SWAP": [1, 30],  # 1–30%
    "BEBOP": {
        "SWAP_ALL_TO_ETH": False,
        "API_URL_QUOTE": "https://api.bebop.xyz/router/megaethtestnet/v1/quote",
        "API_URL_ORDER": "https://api.bebop.xyz/pmm/megaethtestnet/v3/order",
        "API_TIMEOUT": 10
    }
}