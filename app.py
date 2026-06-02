from __future__ import annotations

from flask import Flask, Response

import config
from radar import run_radar

app = Flask(__name__)


def money(value: float) -> str:
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.2f}"


@app.get("/")
def index() -> Response:
    try:
        items = run_radar()
        lines = []
        lines.append("SOLANA MEME RADAR - TEXT ONLY")
        lines.append("Refresh browser to rescan.")
        lines.append("")
        lines.append("Filters:")
        lines.append(f"- Age: >={config.MIN_AGE_DAYS} days")
        lines.append(f"- Liquidity: >={money(config.MIN_LIQUIDITY_USD)}")
        lines.append(f"- Market cap: {money(config.MIN_MARKET_CAP_USD)} to {money(config.MAX_MARKET_CAP_USD)}")
        lines.append(f"- Volume 24h: >={money(config.MIN_VOLUME_24H_USD)}")
        lines.append("")
        if not items:
            lines.append("No candidates found. Try lowering filters in config.py.")
        for c in items:
            lines.append("=" * 80)
            lines.append(f"#{c.rank} {c.symbol} - {c.name}")
            lines.append(f"Score: {c.score}/100 | Risk: {c.risk_label} | Smart Money Proxy: {c.smart_money_score}/100")
            lines.append(f"Age: {c.age_days}d | MC: {money(c.market_cap_usd)} | Liq: {money(c.liquidity_usd)} | Vol24h: {money(c.volume_24h_usd)}")
            lines.append(f"Txns24h: {c.txns_24h} | Buys: {c.buys_24h} | Sells: {c.sells_24h}")
            lines.append(f"Price: ${c.price_usd:.12f}")
            lines.append(f"Change 24h: {c.price_change_24h}% | Change 7d: {c.price_change_7d}%")
            lines.append(f"Token: {c.token_address}")
            lines.append(f"Chart: {c.url}")
            lines.append(f"Notes: {c.notes}")
        lines.append("")
        lines.append("Disclaimer: This is not financial advice. Smart Money Proxy is heuristic until real wallet data is connected.")
        return Response("\n".join(lines), mimetype="text/plain")
    except Exception as exc:
        return Response(f"Radar error: {exc}\n", mimetype="text/plain", status=500)


if __name__ == "__main__":
    print(f"Open http://{config.HOST}:{config.PORT}/")
    app.run(host=config.HOST, port=config.PORT, debug=True)
