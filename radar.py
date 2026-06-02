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
    risk_label: str
    notes: str


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
    # DexScreener returns milliseconds.
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


def passes_filters(pair: dict[str, Any]) -> bool:
    age = _pair_age_days(pair)
    liquidity = _to_float((pair.get("liquidity") or {}).get("usd"))
    market_cap = _to_float(pair.get("marketCap") or pair.get("fdv"))
    volume_24h = _to_float((pair.get("volume") or {}).get("h24"))
    txns = pair.get("txns") or {}
    txns_24h = _to_int((txns.get("h24") or {}).get("buys")) + _to_int((txns.get("h24") or {}).get("sells"))

    return (
        age >= config.MIN_AGE_DAYS
        and age <= config.MAX_AGE_DAYS
        and liquidity >= config.MIN_LIQUIDITY_USD
        and market_cap >= config.MIN_MARKET_CAP_USD
        and market_cap <= config.MAX_MARKET_CAP_USD
        and volume_24h >= config.MIN_VOLUME_24H_USD
        and txns_24h >= config.MIN_TXNS_24H
    )


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def log_score(value: float, low: float, high: float) -> float:
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return clamp((math.log10(value) - math.log10(low)) / (math.log10(high) - math.log10(low)))


def score_pair(pair: dict[str, Any]) -> tuple[float, dict[str, float], str, str]:
    age = _pair_age_days(pair)
    liquidity = _to_float((pair.get("liquidity") or {}).get("usd"))
    market_cap = _to_float(pair.get("marketCap") or pair.get("fdv"))
    volume_24h = _to_float((pair.get("volume") or {}).get("h24"))
    volume_6h = _to_float((pair.get("volume") or {}).get("h6"))
    txns = pair.get("txns") or {}
    buys_24h = _to_int((txns.get("h24") or {}).get("buys"))
    sells_24h = _to_int((txns.get("h24") or {}).get("sells"))
    txns_24h = buys_24h + sells_24h
    pc = pair.get("priceChange") or {}
    price_change_24h = _to_float(pc.get("h24"))
    price_change_7d = _to_float(pc.get("d7"))

    buy_pressure = buys_24h / max(1, txns_24h)
    volume_accel = volume_6h * 4 / max(1, volume_24h)

    parts = {
        "age": clamp((age - 30) / 60),
        "liquidity": log_score(liquidity, 100_000, 2_000_000),
        "market_cap": 1.0 - clamp((market_cap - 500_000) / 49_500_000),
        "volume": log_score(volume_24h, 20_000, 2_000_000),
        "txns": log_score(txns_24h, 50, 5_000),
        "price_momentum": clamp((price_change_24h + 10) / 60),
        "buy_pressure": clamp((buy_pressure - 0.45) / 0.20),
        "revival": clamp((-price_change_7d + 60) / 120) if price_change_7d < 0 and price_change_24h > -5 else 0.3,
        # Placeholder until you connect real smart-wallet data.
        "smart_money_placeholder": clamp((volume_accel - 0.8) / 1.2),
    }

    total_weight = sum(config.WEIGHTS.values())
    score = sum(parts[k] * config.WEIGHTS[k] for k in config.WEIGHTS) / total_weight * 100

    risk = "LOW" if liquidity > 500_000 and market_cap > 1_000_000 else "MEDIUM"
    if liquidity < 150_000 or market_cap < 300_000:
        risk = "HIGH"

    notes = []
    if parts["smart_money_placeholder"] > 0.7:
        notes.append("possible fresh accumulation via volume acceleration")
    if buy_pressure > 0.58:
        notes.append("buy pressure strong")
    if price_change_7d < -40 and price_change_24h > -5:
        notes.append("possible revival setup")
    if not notes:
        notes.append("passes base filters")

    return round(score, 2), parts, risk, "; ".join(notes)


def make_candidate(pair: dict[str, Any], rank: int, score: float, risk: str, notes: str) -> Candidate:
    base = pair.get("baseToken") or {}
    txns = pair.get("txns") or {}
    pc = pair.get("priceChange") or {}
    buys_24h = _to_int((txns.get("h24") or {}).get("buys"))
    sells_24h = _to_int((txns.get("h24") or {}).get("sells"))
    return Candidate(
        rank=rank,
        score=score,
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
        smart_money_score=round(score_pair(pair)[1]["smart_money_placeholder"] * 100, 2),
        risk_label=risk,
        notes=notes,
    )


def run_radar() -> list[Candidate]:
    pairs = fetch_solana_pairs()
    scored = []
    for pair in pairs:
        if not passes_filters(pair):
            continue
        score, _parts, risk, notes = score_pair(pair)
        scored.append((score, pair, risk, notes))
    scored.sort(key=lambda x: x[0], reverse=True)
    candidates = [make_candidate(pair, i + 1, score, risk, notes) for i, (score, pair, risk, notes) in enumerate(scored[: config.TOP_N])]
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
