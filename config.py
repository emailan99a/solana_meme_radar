import os

# Render
PORT = int(os.environ.get("PORT", 8765))
HOST = "0.0.0.0"

# Radar Filters
SEARCH_TERMS = [
    "meme",
    "dog",
    "cat",
    "pepe",
    "ai",
    "sol",
    "coin",
]

MIN_AGE_DAYS = 30
MIN_LIQUIDITY_USD = 100_000
MIN_MARKET_CAP_USD = 100_000
MAX_MARKET_CAP_USD = 50_000_000
MIN_VOLUME_24H_USD = 20_000
MIN_TXNS_24H = 100

TOP_N = 10
