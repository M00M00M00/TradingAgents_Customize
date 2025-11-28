"""
Indicator calculations from OHLCV dataframes for crypto short-term analysis.

This module avoids external TA dependencies to keep tests offline-friendly.
"""
from __future__ import annotations

import pandas as pd


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a bundle of indicators: SMA(7/25/99), RSI(14), Bollinger(20,2), MACD(12,26,9).
    Assumes df has columns: datetime, open, high, low, close, volume.
    """
    out = df.copy()
    close = out["close"]

    # SMA
    out["sma_7"] = close.rolling(window=7, min_periods=7).mean()
    out["sma_25"] = close.rolling(window=25, min_periods=25).mean()
    out["sma_99"] = close.rolling(window=99, min_periods=99).mean()

    # RSI 14
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=14, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14, min_periods=14).mean()
    rs = gain / loss.replace(0, pd.NA)
    out["rsi_14"] = 100 - (100 / (1 + rs))

    # Bollinger 20,2
    rolling_mean = close.rolling(window=20, min_periods=20).mean()
    rolling_std = close.rolling(window=20, min_periods=20).std()
    out["bb_mid_20"] = rolling_mean
    out["bb_upper_20_2"] = rolling_mean + 2 * rolling_std
    out["bb_lower_20_2"] = rolling_mean - 2 * rolling_std

    # MACD 12/26/9
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd = ema12 - ema26
    signal = _ema(macd, 9)
    out["macd"] = macd
    out["macd_signal"] = signal
    out["macd_hist"] = macd - signal

    return out


def indicators_summary(df: pd.DataFrame, tail: int = 5) -> str:
    """
    Produce a compact textual summary of the latest indicator values.
    """
    tail_df = df.tail(tail)
    latest = tail_df.iloc[-1]

    summary_lines = [
        "# Indicators summary (latest bar)",
        f"close={latest['close']}",
        f"sma7={latest.get('sma_7')}, sma25={latest.get('sma_25')}, sma99={latest.get('sma_99')}",
        f"rsi14={latest.get('rsi_14')}",
        f"bb_upper={latest.get('bb_upper_20_2')}, bb_mid={latest.get('bb_mid_20')}, bb_lower={latest.get('bb_lower_20_2')}",
        f"macd={latest.get('macd')}, macd_signal={latest.get('macd_signal')}, macd_hist={latest.get('macd_hist')}",
    ]
    return "\n".join(str(x) for x in summary_lines)
