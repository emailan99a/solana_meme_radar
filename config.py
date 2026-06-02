PORT = 8765
HOST = "127.0.0.1"

MIN_AGE_DAYS = 30
MAX_AGE_DAYS = 365
MIN_LIQUIDITY_USD = 100_000
MAX_MARKET_CAP_USD = 50_000_000
MIN_MARKET_CAP_USD = 100_000
MIN_VOLUME_24H_USD = 20_000
MIN_TXNS_24H = 50
TOP_N = 10

SEARCH_TERMS = [
    "solana meme",
    "pump solana",
    "pumpfun solana",
    "dog solana",
    "cat solana",
    "frog solana",
    "ai solana",
    "pepe solana",
    "bonk solana",
    "wif solana",
    "goat solana",
    "trenches solana",
]

WEIGHTS = {
    "age": 8,
    "liquidity": 12,
    "market_cap": 8,
    "volume": 10,
    "txns": 8,
    "price_momentum": 8,
    "buy_pressure": 10,
    "revival": 8,
    "smart_money_placeholder": 12,
    "volume_spike": 6,
    "whale_entry": 5,
    "accumulation": 5,
}

FALLBACK_MIN_LIQUIDITY_USD = 50_000
FALLBACK_MIN_MARKET_CAP_USD = 50_000
FALLBACK_MIN_VOLUME_24H_USD = 10_000
FALLBACK_MIN_TXNS_24H = 25
FALLBACK_SCORE_PENALTY = 8
