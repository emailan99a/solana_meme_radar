import os

# Render
PORT = int(os.environ.get("PORT", 8765))
HOST = "0.0.0.0"

# Radar Filters
SEARCH_TERMS = [
    "dog",
    "cat",
    "pepe",
    "bonk",
    "meme",
    "ai",
    "sol",
    "pump",
    "moon",
    "frog"
]

MIN_AGE_DAYS = 7
MIN_LIQUIDITY_USD = 25000
MIN_VOLUME_24H_USD = 5000
MIN_TXNS_24H = 20

TOP_N = 10
