from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

import requests

import config

DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"


@dataclass
class Candidate:
    rank: int
    score: float
    confidence_score: float
    symbol: str
    name: str
    token_address: str
    pair_address: str
    url: str
    age_days: float
    price_usd: float
    liquidity_usd: float
    market_cap_usd: float
    volume_24h_usd: float
    txns_24h: int
    buys_24h: int
    sells_24h: int
    price_change_24h: float
    price_change_7d: float
    smart_money_score: float
    volume_spike_score: float
    whale_entry_score: float
    accumulation_score: float
    risk_label: str
    notes: str
    elliott_wave: str
    fib_zone: str
    estimated_bottom: float
    estimated_top: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    setup_label: str
    watchlist_signal: str


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _pair_age_days(pair: dict[str, Any]) -> float:
    created_at = pair.get("pairCreatedAt")
    if not created_at:
        return 0.0
    seconds = int(created_at) / 1000
    return max(0.0, (time.time() - seconds) / 86400)


def _fetch_pairs_for_term(term: str) -> list[dict[str, Any]]:
    response = requests.get(DEX_SEARCH_URL, params={"q": term}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("pairs") or []


def fetch_solana_pairs() -> list[dict[str, Any]]:
    seen = set()
    pairs: list[dict[str, Any]] = []
    for term in config.SEARCH_TERMS:
        try:
            for pair in _fetch_pairs_for_term(term):
                if pair.get("chainId") != "solana":
                    continue
                key = pair.get("pairAddress")
                if not key or key in seen:
                    continue
                seen.add(key)
                pairs.append(pair)
        except Exception as exc:
            print(f"Fetch failed for {term}: {exc}")
    return pairs


def filter_level(pair: dict[str, Any]) -> int:
    age = _pair_age_days(pair)
    liquidity = _to_float((pair.get("liquidity") or {}).get("usd"))
    market_cap = _to_float(pair.get("marketCap") or pair.get("fdv"))
    volume_24h = _to_float((pair.get("volume") or {}).get("h24"))
    txns = pair.get("txns") or {}
    txns_24h = _to_int((txns.get("h24") or {}).get("buys")) + _to_int((txns.get("h24") or {}).get("sells"))

    strict = (
        age >= config.MIN_AGE_DAYS
        and age <= config.MAX_AGE_DAYS
        and liquidity >= config.MIN_LIQUIDITY_USD
        and market_cap >= config.MIN_MARKET_CAP_USD
        and market_cap <= config.MAX_MARKET_CAP_USD
        and volume_24h >= config.MIN_VOLUME_24H_USD
        and txns_24h >= config.MIN_TXNS_24H
    )
    if strict:
        return 2

    near_pass = (
        age >= config.MIN_AGE_DAYS
        and age <= config.MAX_AGE_DAYS
        and liquidity >= config.FALLBACK_MIN_LIQUIDITY_USD
        and market_cap >= config.FALLBACK_MIN_MARKET_CAP_USD
        and market_cap <= config.MAX_MARKET_CAP_USD
        and volume_24h >= config.FALLBACK_MIN_VOLUME_24H_USD
        and txns_24h >= config.FALLBACK_MIN_TXNS_24H
    )
    if near_pass:
        return 1
    return 0


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def log_score(value: float, low: float, high: float) -> float:
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return clamp((math.log10(value) - math.log10(low)) / (math.log10(high) - math.log10(low)))


def analyze_pair(pair: dict[str, Any]) -> tuple[float, dict[str, float], str, str, dict[str, Any]]:
    age = _pair_age_days(pair)
    liquidity = _to_float((pair.get("liquidity") or {}).get("usd"))
    market_cap = _to_float(pair.get("marketCap") or pair.get("fdv"))
    volume = pair.get("volume") or {}
    volume_24h = _to_float(volume.get("h24"))
    volume_6h = _to_float(volume.get("h6"))
    volume_1h = _to_float(volume.get("h1"))
    txns = pair.get("txns") or {}
    buys_24h = _to_int((txns.get("h24") or {}).get("buys"))
    sells_24h = _to_int((txns.get("h24") or {}).get("sells"))
    txns_24h = buys_24h + sells_24h
    pc = pair.get("priceChange") or {}
    price_change_24h = _to_float(pc.get("h24"))
    price_change_7d = _to_float(pc.get("d7"))
    price = _to_float(pair.get("priceUsd"))

    buy_pressure = buys_24h / max(1, txns_24h)
    volume_accel_6h = volume_6h * 4 / max(1, volume_24h)
    volume_accel_1h = volume_1h * 24 / max(1, volume_24h)

    smart_money_score = clamp((volume_accel_6h - 0.75) / 1.25) * 55 + clamp((buy_pressure - 0.50) / 0.18) * 35 + log_score(volume_24h, 50_000, 5_000_000) * 10
    volume_spike_score = clamp(max(volume_accel_6h, volume_accel_1h) / 3.0) * 100
    avg_buy_size = (volume_24h * buy_pressure) / max(1, buys_24h)
    whale_entry_score = clamp(avg_buy_size / 2500) * 45 + clamp((liquidity / max(1, market_cap)) / 0.35) * 25 + clamp((buy_pressure - 0.52) / 0.18) * 30
    accumulation_score = clamp((buy_pressure - 0.50) / 0.18) * 40 + clamp((volume_accel_6h - 0.85) / 1.25) * 35 + clamp((15 - abs(price_change_24h)) / 15) * 25

    parts = {
        "age": clamp((age - 30) / 60),
        "liquidity": log_score(liquidity, 100_000, 2_000_000),
        "market_cap": 1.0 - clamp((market_cap - 500_000) / 49_500_000),
        "volume": log_score(volume_24h, 20_000, 2_000_000),
        "txns": log_score(txns_24h, 50, 5_000),
        "price_momentum": clamp((price_change_24h + 10) / 60),
        "buy_pressure": clamp((buy_pressure - 0.45) / 0.20),
        "revival": clamp((-price_change_7d + 60) / 120) if price_change_7d < 0 and price_change_24h > -8 else 0.3,
        "smart_money_placeholder": clamp(smart_money_score / 100),
        "volume_spike": clamp(volume_spike_score / 100),
        "whale_entry": clamp(whale_entry_score / 100),
        "accumulation": clamp(accumulation_score / 100),
    }

    total_weight = sum(config.WEIGHTS.values())
    score = sum(parts[k] * config.WEIGHTS[k] for k in config.WEIGHTS) / total_weight * 100

    risk = "LOW" if liquidity > 500_000 and market_cap > 1_000_000 else "MEDIUM"
    if liquidity < 150_000 or market_cap < 300_000:
        risk = "HIGH"

    notes = []
    if smart_money_score >= 70:
        notes.append("fresh smart-money proxy is strong")
    elif smart_money_score >= 45:
        notes.append("fresh smart-money proxy is moderate")
    if volume_spike_score >= 65:
        notes.append("volume spike detected")
    if whale_entry_score >= 60:
        notes.append("possible whale entry")
    if accumulation_score >= 65:
        notes.append("fresh accumulation alert")
    if buy_pressure > 0.58:
        notes.append("buy pressure strong")
    if price_change_7d < -35 and price_change_24h > -8:
        notes.append("possible revival setup")
    if not notes:
        notes.append("passes base filters")

    rr = build_trade_plan(price, price_change_24h, price_change_7d, volume_accel_6h, accumulation_score)
    extra = {
        "smart_money_score": round(clamp(smart_money_score, 0, 100), 2),
        "volume_spike_score": round(clamp(volume_spike_score, 0, 100), 2),
        "whale_entry_score": round(clamp(whale_entry_score, 0, 100), 2),
        "accumulation_score": round(clamp(accumulation_score, 0, 100), 2),
        **rr,
    }
    return round(score, 2), parts, risk, "; ".join(notes), extra


def build_trade_plan(price: float, change_24h: float, change_7d: float, volume_accel: float, accumulation_score: float) -> dict[str, Any]:
    if price <= 0:
        price = 0.000000001

    if change_7d < -35 and change_24h > -10:
        setup = "Revival / Wave 1 candidate"
        wave = "Potential Wave 1 after deep correction. Wait for Wave 2 pullback before heavy entry."
        bottom_mult = 0.82
        top_mult = 1.90
    elif accumulation_score >= 65 and abs(change_24h) < 25:
        setup = "Accumulation base / possible Wave 2 ending"
        wave = "Potential base before Wave 3. Bullish only while price holds above invalidation."
        bottom_mult = 0.88
        top_mult = 2.20
    elif change_24h > 25:
        setup = "Momentum / possible Wave 3"
        wave = "Possible Wave 3 expansion. Avoid chasing if price extends too far above entry."
        bottom_mult = 0.90
        top_mult = 1.75
    else:
        setup = "Neutral watchlist"
        wave = "No clean impulse yet. Treat as watchlist until volume and buy pressure improve."
        bottom_mult = 0.86
        top_mult = 1.65

    estimated_bottom = price * bottom_mult
    estimated_top = price * top_mult

    # Fib heuristic: use current price as entry proxy, SL below 0.786 zone, TP near 1.618 extension.
    entry = price
    stop = min(price * 0.82, estimated_bottom * 0.98)
    risk = max(entry - stop, price * 0.01)
    tp1 = entry + risk * 2.05
    tp2 = entry + risk * 3.10
    if tp1 > estimated_top:
        estimated_top = tp2 * 1.05

    fib_zone = "Entry zone: 0.5-0.618 retrace; invalidation below 0.786; TP near 1.618-2.618 extension."
    rr = (tp1 - entry) / max(0.0000000001, entry - stop)

    watchlist = "WATCH"
    if accumulation_score >= 65 and rr >= 2:
        watchlist = "HIGH PRIORITY"
    elif rr >= 2 and volume_accel >= 1.2:
        watchlist = "MEDIUM PRIORITY"

    return {
        "setup_label": setup,
        "elliott_wave": wave,
        "fib_zone": fib_zone,
        "estimated_bottom": estimated_bottom,
        "estimated_top": estimated_top,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": tp1,
        "take_profit_2": tp2,
        "risk_reward": rr,
        "watchlist_signal": watchlist,
    }


def make_candidate(pair: dict[str, Any], rank: int, score: float, risk: str, notes: str, extra: dict[str, Any]) -> Candidate:
    base = pair.get("baseToken") or {}
    txns = pair.get("txns") or {}
    pc = pair.get("priceChange") or {}
    buys_24h = _to_int((txns.get("h24") or {}).get("buys"))
    sells_24h = _to_int((txns.get("h24") or {}).get("sells"))
    return Candidate(
        rank=rank,
        score=score,
        confidence_score=round(score / 10, 2),
        symbol=base.get("symbol") or "?",
        name=base.get("name") or "?",
        token_address=base.get("address") or "?",
        pair_address=pair.get("pairAddress") or "?",
        url=pair.get("url") or "",
        age_days=round(_pair_age_days(pair), 1),
        price_usd=_to_float(pair.get("priceUsd")),
        liquidity_usd=round(_to_float((pair.get("liquidity") or {}).get("usd")), 2),
        market_cap_usd=round(_to_float(pair.get("marketCap") or pair.get("fdv")), 2),
        volume_24h_usd=round(_to_float((pair.get("volume") or {}).get("h24")), 2),
        txns_24h=buys_24h + sells_24h,
        buys_24h=buys_24h,
        sells_24h=sells_24h,
        price_change_24h=round(_to_float(pc.get("h24")), 2),
        price_change_7d=round(_to_float(pc.get("d7")), 2),
        smart_money_score=extra["smart_money_score"],
        volume_spike_score=extra["volume_spike_score"],
        whale_entry_score=extra["whale_entry_score"],
        accumulation_score=extra["accumulation_score"],
        risk_label=risk,
        notes=notes,
        elliott_wave=extra["elliott_wave"],
        fib_zone=extra["fib_zone"],
        estimated_bottom=extra["estimated_bottom"],
        estimated_top=extra["estimated_top"],
        entry_price=extra["entry_price"],
        stop_loss=extra["stop_loss"],
        take_profit_1=extra["take_profit_1"],
        take_profit_2=extra["take_profit_2"],
        risk_reward=round(extra["risk_reward"], 2),
        setup_label=extra["setup_label"],
        watchlist_signal=extra["watchlist_signal"],
    )


def run_radar() -> list[Candidate]:
    pairs = fetch_solana_pairs()
    scored = []
    for pair in pairs:
        level = filter_level(pair)
        if level == 0:
            continue
        score, _parts, risk, notes, extra = analyze_pair(pair)
        if extra["risk_reward"] < 2.0:
            score -= 12
            notes = f"RR under 2.0 filtered down; {notes}"
        if level == 1:
            score = max(0.0, score - config.FALLBACK_SCORE_PENALTY)
            notes = f"near-pass fallback; {notes}"
        scored.append((score, pair, risk, notes, extra))

    scored.sort(key=lambda x: x[0], reverse=True)
    candidates = [
        make_candidate(pair, i + 1, score, risk, notes, extra)
        for i, (score, pair, risk, notes, extra) in enumerate(scored[: config.TOP_N])
    ]
    save_snapshot(candidates)
    return candidates


def save_snapshot(candidates: list[Candidate]) -> None:
    os.makedirs("data", exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "count": len(candidates),
        "items": [asdict(c) for c in candidates],
    }
    with open("data/snapshots.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
