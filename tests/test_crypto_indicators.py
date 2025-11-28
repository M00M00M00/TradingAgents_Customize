import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tradingagents.dataflows.crypto_indicators import compute_indicators, indicators_summary


def sample_df(rows=120):
    data = {
        "datetime": pd.date_range("2024-01-01", periods=rows, freq="15min"),
        "open": [100 + i * 0.1 for i in range(rows)],
        "high": [101 + i * 0.1 for i in range(rows)],
        "low": [99 + i * 0.1 for i in range(rows)],
        "close": [100 + i * 0.1 for i in range(rows)],
        "volume": [10 + i for i in range(rows)],
    }
    return pd.DataFrame(data)


def test_compute_indicators_adds_columns():
    df = sample_df()
    out = compute_indicators(df)
    for col in ["sma_7", "sma_25", "sma_99", "rsi_14", "bb_upper_20_2", "macd", "macd_signal", "macd_hist"]:
        assert col in out.columns


def test_indicators_summary_returns_text():
    df = compute_indicators(sample_df())
    text = indicators_summary(df)
    assert "Indicators summary" in text
    assert "sma7" in text
