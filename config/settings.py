# config/settings.py
SETTINGS = {
    "THREADS": 1,
    "ATTEMPTS": 5,
    "PAUSE_BETWEEN_SWAPS": [0, 0],
    "SWAPS_AMOUNT": [1, 1],
    "BALANCE_PERCENTAGE_TO_SWAP": [5, 15],  # Изменили на 5–15%
    "BEBOP": {
        "SWAP_ALL_TO_ETH": False,
        "API_URL_QUOTE": "https://api.bebop.xyz/router/megaethtestnet/v1/quote",
        "API_URL_ORDER": "https://api.bebop.xyz/pmm/megaethtestnet/v3/order",
        "API_TIMEOUT": 10
    }
}