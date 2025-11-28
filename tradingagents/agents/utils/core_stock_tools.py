from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_stock_data(
    symbol: Annotated[str, "symbol of the crypto perp contract, e.g. BTC/USDT"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    timeframe: Annotated[str, "timeframe such as 15m or 1h"] = "15m",
) -> str:
    """
    Retrieve OHLCV data for a given crypto symbol from the configured vendor (Bybit via ccxt).
    Args:
        symbol (str): Perp symbol, e.g. BTC/USDT
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
        timeframe (str): CCXT timeframe (default 15m)
    Returns:
        str: A formatted CSV string containing OHLCV for the specified symbol/timeframe.
    """
    return route_to_vendor("get_stock_data", symbol, start_date, end_date, timeframe=timeframe)
