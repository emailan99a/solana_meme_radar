# Solana Meme Radar

Text-only local web app for ranking Solana meme coin candidates.

Important: this MVP uses public DexScreener data plus heuristic scoring. True smart-money wallet tracking needs a paid/on-chain data source such as Birdeye, GMGN, Nansen, Helius-indexed data, or your own wallet database. The app includes placeholder fields and scoring hooks so those signals can be added later.

## Run locally

```bash
cd solana_meme_radar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open:

```text
http://127.0.0.1:8765/
```

Refresh the browser to fetch a new radar scan.

## What it does

- Searches Solana pairs from DexScreener.
- Filters by age, liquidity, market cap, and transaction activity.
- Scores each token using text-only rules.
- Shows Top 10 candidates.
- Saves every scan snapshot to `data/snapshots.jsonl`.

## Edit config

Open `config.py` to adjust filters and scoring weights.
