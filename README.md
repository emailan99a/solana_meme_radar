# Solana Meme Radar

Text-first Flask web app for local Solana meme coin radar.

## Run

```bash
cd ~/Documents/Dev_Projects/solana_meme_radar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open:

```text
http://127.0.0.1:8765/
```

## V3 features

- Top 10 candidates sorted by score
- Score shown as `/10`
- Smart Money Proxy
- Volume Spike Score
- Whale Entry Detection
- Fresh Accumulation Alert
- Watchlist priority
- Elliott Wave heuristic
- Fibonacci heuristic
- Estimated top and bottom
- Entry, Stop Loss, TP1, TP2
- Risk reward target above 2:1
- Clickable DexScreener links

## Important

This is not financial advice. Current Smart Money and Whale scores are heuristics using public DexScreener data. For stronger accuracy, connect real wallet labels, holder data, and OHLC candle data later.
