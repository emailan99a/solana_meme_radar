import os

# Render
PORT = int(os.environ.get("PORT", 8765))
HOST = "0.0.0.0"

# Search
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
    "frog",
]

# Filters
MIN_AGE_DAYS = 7
MAX_AGE_DAYS = 3650

MIN_LIQUIDITY_USD = 25_000

MIN_MARKET_CAP_USD = 100_000
MAX_MARKET_CAP_USD = 50_000_000

MIN_VOLUME_24H_USD = 5_000

MIN_TXNS_24H = 20

TOP_N = 10
