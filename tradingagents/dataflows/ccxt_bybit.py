"""
CCXT-based data access for Bybit USDT perpetual markets.

Network calls are only made when no client is injected. In tests, pass a dummy
client with a `fetch_ohlcv`/`fetch_order_book`/`fetch_funding_rate` method to
avoid network usage.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, List, Optional

import pandas as pd

try:
    import ccxt  # type: ignore
except ImportError:  # pragma: no cover - handled by test injection
    ccxt = None


def _ensure_client():
    if ccxt is None:
        raise RuntimeError(
            "ccxt is required for live data. Install ccxt or inject a client in tests."
        )
    return ccxt.bybit()


def _parse_dates_to_limit(start_date: str, end_date: str, timeframe: str) -> int:
    """Convert date range to an approximate bar count."""
    start = dt.datetime.strptime(start_date, "%Y-%m-%d")
    end = dt.datetime.strptime(end_date, "%Y-%m-%d")
    delta_minutes = (end - start).total_seconds() / 60.0
    tf_map = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }
    minutes_per_bar = tf_map.get(timeframe, 15)
    limit = int(delta_minutes / minutes_per_bar) + 10  # small buffer
    return max(limit, 50)


def get_ohlcv_bybit(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "15m",
    client: Any = None,
) -> str:
    """
    Fetch OHLCV for a symbol between dates (approximate by limit) from Bybit.

    Args:
        symbol: e.g., "BTC/USDT"
        start_date: "YYYY-MM-DD"
        end_date: "YYYY-MM-DD"
        timeframe: ccxt timeframe, default 15m
        client: optional ccxt.bybit instance (for tests, pass a dummy)
    Returns:
        CSV-formatted string with header
    """
    limit = _parse_dates_to_limit(start_date, end_date, timeframe)
    c = client or _ensure_client()
    ohlcv: List[List[Any]] = c.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    if not ohlcv:
        return f"# No data returned for {symbol} {timeframe}\n"

    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df[["datetime", "open", "high", "low", "close", "volume"]]

    header = f"# Bybit OHLCV for {symbol} timeframe={timeframe} rows={len(df)}\n"
    return header + df.to_csv(index=False)


def get_orderbook_window(
    symbol: str,
    client: Any = None,
    price_window_pct: float = 0.005,
) -> str:
    """
    Fetch orderbook and summarize imbalance within +/- price_window_pct.
    """
    c = client or _ensure_client()
    ob = c.fetch_order_book(symbol)
    if not ob or "bids" not in ob or "asks" not in ob or not ob["bids"] or not ob["asks"]:
        return f"# No orderbook data for {symbol}\n"

    best_bid = ob["bids"][0][0]
    best_ask = ob["asks"][0][0]
    mid = (best_bid + best_ask) / 2.0
    lower = mid * (1 - price_window_pct)
    upper = mid * (1 + price_window_pct)

    bid_vol = sum(v for p, v in ob["bids"] if lower <= p <= upper)
    ask_vol = sum(v for p, v in ob["asks"] if lower <= p <= upper)
    imbalance = (bid_vol - ask_vol) / max(bid_vol + ask_vol, 1e-9)

    return (
        f"# Orderbook window +/-{price_window_pct*100:.2f}% for {symbol}\n"
        f"best_bid={best_bid}, best_ask={best_ask}, mid={mid}\n"
        f"bid_volume={bid_vol}, ask_volume={ask_vol}, imbalance={imbalance:.3f}\n"
    )


def get_funding_rate(symbol: str, client: Any = None) -> str:
    """Fetch latest funding rate if supported by ccxt."""
    c = client or _ensure_client()
    try:
        funding = c.fetch_funding_rate(symbol)
    except Exception as e:  # pragma: no cover - ccxt specific
        return f"# Funding rate unavailable for {symbol}: {e}"

    rate = funding.get("fundingRate")
    ts = funding.get("timestamp")
    ts_str = pd.to_datetime(ts, unit="ms") if ts else "unknown"
    return f"# Funding rate for {symbol}: {rate} at {ts_str}"


def get_open_interest_change(
    symbol: str,
    timeframe: str = "1h",
    client: Any = None,
) -> str:
    """
    Fetch open interest history and compute last change.
    """
    c = client or _ensure_client()
    try:
        history = c.fetch_open_interest_history(symbol, timeframe=timeframe, limit=30)
    except Exception as e:  # pragma: no cover - ccxt specific
        return f"# Open interest unavailable for {symbol}: {e}"

    if not history or len(history) < 2:
        return f"# Open interest insufficient data for {symbol}\n"

    latest = history[-1]["openInterestAmount"]
    prev = history[-2]["openInterestAmount"]
    change = latest - prev
    pct = (change / prev) * 100 if prev else 0.0
    return (
        f"# Open interest change for {symbol} ({timeframe}):\n"
        f"latest={latest}, previous={prev}, change={change}, change_pct={pct:.2f}%"
    )
