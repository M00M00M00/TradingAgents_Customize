import datetime as dt
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tradingagents.dataflows.ccxt_bybit import get_ohlcv_bybit


class DummyClient:
    def __init__(self):
        # timestamp, open, high, low, close, volume
        self.data = [
            [dt.datetime(2024, 1, 1, 0, 0).timestamp() * 1000, 100, 110, 95, 105, 10],
            [dt.datetime(2024, 1, 1, 0, 15).timestamp() * 1000, 105, 115, 100, 112, 12],
            [dt.datetime(2024, 1, 1, 0, 30).timestamp() * 1000, 112, 118, 108, 115, 9],
        ]

    def fetch_ohlcv(self, symbol, timeframe="15m", limit=100):
        return self.data


def test_get_ohlcv_bybit_formats_csv():
    client = DummyClient()
    output = get_ohlcv_bybit("BTC/USDT", "2024-01-01", "2024-01-02", timeframe="15m", client=client)

    # Header + CSV rows expected
    assert "Bybit OHLCV for BTC/USDT" in output
    assert "datetime,open,high,low,close,volume" in output
    assert "2024-01-01" in output
