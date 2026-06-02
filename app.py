from __future__ import annotations

from html import escape
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


def price(value: float) -> str:
    if value >= 1:
        return f"${value:.4f}"
    return f"${value:.12f}".rstrip("0")


def pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def risk_class(label: str) -> str:
    label = label.lower()
    if label == "low":
        return "risk-low"
    if label == "medium":
        return "risk-medium"
    return "risk-high"


def score_badge(value: float) -> str:
    score10 = value / 10
    if score10 >= 7:
        cls = "good"
    elif score10 >= 5:
        cls = "mid"
    else:
        cls = "bad"
    return f'<span class="score-pill {cls}">{score10:.1f}/10</span>'


@app.get("/")
def index() -> Response:
    try:
        items = run_radar()
        cards = []
        for c in items:
            cards.append(f"""
            <article class="card">
                <div class="rank">#{c.rank}</div>
                <div class="main">
                    <div class="topline">
                        <div>
                            <div class="watch">{escape(c.watchlist_signal)} · {escape(c.setup_label)}</div>
                            <h2>{escape(c.symbol)} <span>{escape(c.name)}</span></h2>
                            <p class="address">{escape(c.token_address)}</p>
                        </div>
                        <div class="score">
                            <strong>{c.confidence_score:.1f}</strong><span>/10</span>
                            <small>Radar Score</small>
                        </div>
                    </div>

                    <div class="meta">
                        <div><b>Risk</b><span class="pill {risk_class(c.risk_label)}">{escape(c.risk_label)}</span></div>
                        <div><b>Smart Money</b>{score_badge(c.smart_money_score)}</div>
                        <div><b>Volume Spike</b>{score_badge(c.volume_spike_score)}</div>
                        <div><b>Whale Entry</b>{score_badge(c.whale_entry_score)}</div>
                        <div><b>Accumulation</b>{score_badge(c.accumulation_score)}</div>
                    </div>

                    <div class="grid compact">
                        <div><small>Market Cap</small><strong>{money(c.market_cap_usd)}</strong></div>
                        <div><small>Liquidity</small><strong>{money(c.liquidity_usd)}</strong></div>
                        <div><small>Volume 24h</small><strong>{money(c.volume_24h_usd)}</strong></div>
                        <div><small>Age</small><strong>{c.age_days:.1f}d</strong></div>
                        <div><small>Price</small><strong>{price(c.price_usd)}</strong></div>
                        <div><small>Txns 24h</small><strong>{c.txns_24h}</strong></div>
                        <div><small>Buys / Sells</small><strong>{c.buys_24h} / {c.sells_24h}</strong></div>
                        <div><small>Change 24h / 7d</small><strong>{pct(c.price_change_24h)} / {pct(c.price_change_7d)}</strong></div>
                    </div>

                    <section class="trade">
                        <h3>Trade Plan · minimum RR 2:1</h3>
                        <div class="grid trade-grid">
                            <div><small>Entry Proxy</small><strong>{price(c.entry_price)}</strong></div>
                            <div><small>Stop Loss</small><strong>{price(c.stop_loss)}</strong></div>
                            <div><small>TP 1</small><strong>{price(c.take_profit_1)}</strong></div>
                            <div><small>TP 2</small><strong>{price(c.take_profit_2)}</strong></div>
                            <div><small>Risk Reward</small><strong>{c.risk_reward:.2f}:1</strong></div>
                            <div><small>Est. Bottom</small><strong>{price(c.estimated_bottom)}</strong></div>
                            <div><small>Est. Top</small><strong>{price(c.estimated_top)}</strong></div>
                        </div>
                        <p><b>Elliott Wave:</b> {escape(c.elliott_wave)}</p>
                        <p><b>Fibonacci:</b> {escape(c.fib_zone)}</p>
                    </section>

                    <p class="notes"><b>Notes:</b> {escape(c.notes)}</p>
                    <a class="link" href="{escape(c.url)}" target="_blank" rel="noopener noreferrer">Open DexScreener ↗</a>
                </div>
            </article>
            """)

        html = f"""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Solana Meme Radar</title>
            <style>
                :root {{
                    --bg: #faf8f3;
                    --paper: #ffffff;
                    --text: #151515;
                    --muted: #686868;
                    --line: #e7e1d7;
                    --soft: #f2eee6;
                    --good: #0f7b3f;
                    --mid: #9a6b00;
                    --bad: #b3261e;
                    --blue: #174ea6;
                }}
                * {{ box-sizing: border-box; }}
                body {{
                    margin: 0;
                    background: var(--bg);
                    color: var(--text);
                    font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
                    line-height: 1.45;
                }}
                .wrap {{ max-width: 1180px; margin: 0 auto; padding: 36px 20px 56px; }}
                header {{ margin-bottom: 28px; }}
                h1 {{ font-size: 46px; line-height: 1; margin: 0 0 8px; letter-spacing: -1.9px; font-weight: 900; }}
                .subtitle {{ color: var(--muted); font-size: 17px; margin: 0 0 22px; }}
                .toolbar {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
                .button {{
                    display: inline-block;
                    background: #111;
                    color: #fff;
                    padding: 11px 16px;
                    border-radius: 10px;
                    font-weight: 800;
                    text-decoration: none;
                }}
                .filters {{ display: flex; flex-wrap: wrap; gap: 8px; color: var(--muted); font-size: 14px; }}
                .filter {{ background: var(--soft); border: 1px solid var(--line); padding: 8px 10px; border-radius: 999px; }}
                .count {{ font-weight: 900; color: var(--text); }}
                .card {{
                    display: grid;
                    grid-template-columns: 76px 1fr;
                    gap: 18px;
                    background: var(--paper);
                    border: 1px solid var(--line);
                    border-radius: 20px;
                    padding: 22px;
                    margin: 15px 0;
                    box-shadow: 0 1px 0 rgba(0,0,0,.03);
                }}
                .rank {{ font-size: 30px; font-weight: 950; letter-spacing: -1px; color: #333; }}
                .topline {{ display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; }}
                .watch {{ display: inline-block; margin-bottom: 7px; font-size: 12px; font-weight: 900; letter-spacing: .7px; text-transform: uppercase; color: var(--blue); }}
                h2 {{ font-size: 30px; margin: 0; letter-spacing: -0.9px; font-weight: 900; }}
                h2 span {{ font-weight: 650; color: var(--muted); }}
                .address {{ margin: 6px 0 0; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; overflow-wrap: anywhere; }}
                .score {{ min-width: 126px; text-align: right; }}
                .score strong {{ font-size: 44px; line-height: 1; letter-spacing: -1.6px; font-weight: 950; }}
                .score span {{ font-size: 20px; color: var(--muted); font-weight: 800; }}
                .score small {{ display: block; margin-top: 3px; }}
                .meta {{ display: flex; flex-wrap: wrap; gap: 9px; margin: 18px 0; }}
                .meta div {{ display: flex; align-items: center; gap: 8px; background: var(--soft); border-radius: 12px; padding: 9px 11px; }}
                .meta b {{ font-size: 12px; text-transform: uppercase; letter-spacing: .5px; color: var(--muted); }}
                .pill {{ border-radius: 999px; padding: 2px 8px; font-weight: 900; }}
                .risk-low, .good {{ color: var(--good); }}
                .risk-medium, .mid {{ color: var(--mid); }}
                .risk-high, .bad {{ color: var(--bad); }}
                .score-pill {{ font-weight: 900; }}
                .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
                .grid div {{ border-top: 1px solid var(--line); padding-top: 10px; min-width: 0; }}
                small {{ display: block; color: var(--muted); font-weight: 800; font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }}
                .grid strong {{ display: block; font-size: 16px; overflow-wrap: anywhere; font-weight: 850; }}
                .trade {{ margin-top: 18px; background: #fbfaf7; border: 1px solid var(--line); border-radius: 16px; padding: 16px; }}
                .trade h3 {{ margin: 0 0 12px; font-size: 18px; letter-spacing: -.2px; }}
                .trade p {{ margin: 10px 0 0; color: #333; }}
                .trade-grid {{ grid-template-columns: repeat(7, minmax(0, 1fr)); }}
                .notes {{ margin: 18px 0 14px; color: #333; }}
                .link {{ color: #111; font-weight: 900; text-underline-offset: 3px; }}
                .disclaimer {{ margin-top: 26px; color: var(--muted); font-size: 13px; }}
                @media (max-width: 900px) {{
                    h1 {{ font-size: 36px; }}
                    .card {{ grid-template-columns: 1fr; }}
                    .topline {{ flex-direction: column; }}
                    .score {{ text-align: left; }}
                    .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
                    .trade-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
                }}
            </style>
        </head>
        <body>
            <main class="wrap">
                <header>
                    <h1>Solana Meme Radar</h1>
                    <p class="subtitle">Text-first radar for Solana meme coins with accumulation, whale-entry, Elliott Wave, Fibonacci, TP and SL heuristics.</p>
                    <div class="toolbar">
                        <a class="button" href="/">Refresh Radar</a>
                        <div class="filters">
                            <span class="filter"><span class="count">{len(items)}</span> candidates</span>
                            <span class="filter">Age ≥ {config.MIN_AGE_DAYS}d</span>
                            <span class="filter">Liquidity ≥ {money(config.MIN_LIQUIDITY_USD)}</span>
                            <span class="filter">MC {money(config.MIN_MARKET_CAP_USD)} - {money(config.MAX_MARKET_CAP_USD)}</span>
                            <span class="filter">Vol 24h ≥ {money(config.MIN_VOLUME_24H_USD)}</span>
                            <span class="filter">RR target ≥ 2:1</span>
                        </div>
                    </div>
                </header>
                {''.join(cards) if cards else '<p>No candidates found. Try lowering filters in config.py.</p>'}
                <p class="disclaimer">Disclaimer: This is not financial advice. Smart Money, Whale Entry, Elliott Wave, Fibonacci, TP and SL are heuristic estimates from public DexScreener data until real wallet and OHLC candle data are connected. Always verify manually before trading.</p>
            </main>
        </body>
        </html>
        """
        return Response(html, mimetype="text/html")
    except Exception as exc:
        return Response(f"Radar error: {exc}\n", mimetype="text/plain", status=500)


if __name__ == "__main__":
    print(f"Open http://{config.HOST}:{config.PORT}/")
    app.run(host=config.HOST, port=config.PORT, debug=True)
