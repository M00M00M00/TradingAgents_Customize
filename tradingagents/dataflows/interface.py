from typing import Annotated

# Crypto data via Bybit (ccxt)
from .ccxt_bybit import (
    get_ohlcv_bybit,
    get_orderbook_window,
    get_funding_rate,
    get_open_interest_change,
)
from .crypto_indicators import compute_indicators, indicators_summary

# Configuration and routing logic
from .config import get_config

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {  # Retain key to minimize downstream changes
        "description": "Crypto OHLCV data (Bybit via ccxt)",
        "tools": ["get_stock_data"],
    },
    "technical_indicators": {
        "description": "Technical analysis indicators (crypto)",
        "tools": ["get_indicators"],
    },
    "market_micro": {
        "description": "Orderbook, funding, open interest context",
        "tools": ["get_orderbook", "get_funding_rate", "get_open_interest_change"],
    },
}

VENDOR_LIST = [
    "ccxt",
]


def _ccxt_indicators(symbol: str, indicator: str, curr_date: str, look_back_days: int, timeframe: str = "15m") -> str:
    """
    Fetch OHLCV and compute indicator bundle. `indicator` argument is ignored to keep API stable.
    """
    # use the shorter window derived from look_back_days
    from datetime import datetime, timedelta
    end_date = curr_date
    start_dt = datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    csv_data = get_ohlcv_bybit(symbol, start_date, end_date, timeframe=timeframe)
    # Parse back to dataframe for indicators
    df = None
    try:
        df = _csv_to_df(csv_data)
        df = compute_indicators(df)
    except Exception as e:
        return f"# Failed to compute indicators for {symbol}: {e}"

    return indicators_summary(df, tail=5)


def _csv_to_df(csv_str: str):
    import io
    import pandas as pd

    lines = [line for line in csv_str.splitlines() if not line.startswith("#")]
    cleaned = "\n".join(lines)
    if not cleaned.strip():
        raise ValueError("No data to parse for indicators")
    return pd.read_csv(io.StringIO(cleaned))


# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "ccxt": get_ohlcv_bybit,
    },
    # technical_indicators
    "get_indicators": {
        "ccxt": _ccxt_indicators,
    },
    # extra crypto context (exposed via tools only if needed)
    "get_orderbook": {
        "ccxt": get_orderbook_window,
    },
    "get_funding_rate": {
        "ccxt": get_funding_rate,
    },
    "get_open_interest_change": {
        "ccxt": get_open_interest_change,
    },
}

def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")

def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Tool-level configuration takes precedence over category-level.
    """
    config = get_config()

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    return config.get("data_vendors", {}).get(category, "default")

def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support."""
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)

    # Handle comma-separated vendors
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Get all available vendors for this method for fallback
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    
    # Create fallback vendor list: primary vendors first, then remaining vendors as fallbacks
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    # Debug: Print fallback ordering
    primary_str = " → ".join(primary_vendors)
    fallback_str = " → ".join(fallback_vendors)
    print(f"DEBUG: {method} - Primary: [{primary_str}] | Full fallback order: [{fallback_str}]")

    # Track results and execution state
    results = []
    vendor_attempt_count = 0
    any_primary_vendor_attempted = False
    successful_vendor = None

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            if vendor in primary_vendors:
                print(f"INFO: Vendor '{vendor}' not supported for method '{method}', falling back to next vendor")
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        is_primary_vendor = vendor in primary_vendors
        vendor_attempt_count += 1

        # Track if we attempted any primary vendor
        if is_primary_vendor:
            any_primary_vendor_attempted = True

        # Debug: Print current attempt
        vendor_type = "PRIMARY" if is_primary_vendor else "FALLBACK"
        print(f"DEBUG: Attempting {vendor_type} vendor '{vendor}' for {method} (attempt #{vendor_attempt_count})")

        # Handle list of methods for a vendor
        if isinstance(vendor_impl, list):
            vendor_methods = [(impl, vendor) for impl in vendor_impl]
            print(f"DEBUG: Vendor '{vendor}' has multiple implementations: {len(vendor_methods)} functions")
        else:
            vendor_methods = [(vendor_impl, vendor)]

        # Run methods for this vendor
        vendor_results = []
        for impl_func, vendor_name in vendor_methods:
            try:
                print(f"DEBUG: Calling {impl_func.__name__} from vendor '{vendor_name}'...")
                result = impl_func(*args, **kwargs)
                vendor_results.append(result)
                print(f"SUCCESS: {impl_func.__name__} from vendor '{vendor_name}' completed successfully")
            except Exception as e:
                # Log error but continue with other implementations
                print(f"FAILED: {impl_func.__name__} from vendor '{vendor_name}' failed: {e}")
                continue

        # Add this vendor's results
        if vendor_results:
            results.extend(vendor_results)
            successful_vendor = vendor
            result_summary = f"Got {len(vendor_results)} result(s)"
            print(f"SUCCESS: Vendor '{vendor}' succeeded - {result_summary}")
            
            # Stopping logic: Stop after first successful vendor for single-vendor configs
            # Multiple vendor configs (comma-separated) may want to collect from multiple sources
            if len(primary_vendors) == 1:
                print(f"DEBUG: Stopping after successful vendor '{vendor}' (single-vendor config)")
                break
        else:
            print(f"FAILED: Vendor '{vendor}' produced no results")

    # Final result summary
    if not results:
        print(f"FAILURE: All {vendor_attempt_count} vendor attempts failed for method '{method}'")
        raise RuntimeError(f"All vendor implementations failed for method '{method}'")
    else:
        print(f"FINAL: Method '{method}' completed with {len(results)} result(s) from {vendor_attempt_count} vendor attempt(s)")

    # Return single result if only one, otherwise concatenate as string
    if len(results) == 1:
        return results[0]
    else:
        # Convert all results to strings and concatenate
        return '\n'.join(str(result) for result in results)
