from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

@tool
def get_indicators(
    symbol: Annotated[str, "symbol of the crypto perp contract, e.g. BTC/USDT"],
    indicator: Annotated[str, "indicator name (ignored, full bundle returned)"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
    timeframe: Annotated[str, "timeframe for indicators (15m/1h)"] = "15m",
) -> str:
    """
    Retrieve a bundle of technical indicators for a given crypto symbol.
    Uses the configured technical_indicators vendor (Bybit ccxt + pandas).
    Args:
        symbol (str): Perp symbol, e.g. BTC/USDT
        indicator (str): Ignored; kept for backward compatibility
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
        timeframe (str): 15m or 1h (default 15m)
    Returns:
        str: A formatted textual summary of indicator values.
    """
    return route_to_vendor("get_indicators", symbol, indicator, curr_date, look_back_days, timeframe=timeframe)
