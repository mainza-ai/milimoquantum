"""Milimo Quantum — Yahoo Finance Data Feed.

Fetches real market data for the Finance Agent's portfolio optimization.
Uses yfinance (free, no API key required).
Gracefully degrades when yfinance is not installed.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

YFINANCE_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    logger.info("yfinance not installed — using mock market data")


def get_stock_prices(symbols: list[str]) -> dict[str, Any]:
    """Fetch current stock prices for given ticker symbols.

    Returns dict with symbol → {price, change, change_pct, name, currency}.
    """
    if not YFINANCE_AVAILABLE:
        return _mock_prices(symbols)

    results = {}
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            try:
                info = tickers.tickers[sym].info
                results[sym] = {
                    "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
                    "previous_close": info.get("previousClose", 0),
                    "name": info.get("shortName", sym),
                    "currency": info.get("currency", "USD"),
                    "market_cap": info.get("marketCap"),
                    "sector": info.get("sector"),
                }
                if results[sym]["previous_close"]:
                    change = results[sym]["price"] - results[sym]["previous_close"]
                    results[sym]["change"] = round(change, 2)
                    results[sym]["change_pct"] = round(
                        (change / results[sym]["previous_close"]) * 100, 2
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch {sym}: {e}")
                results[sym] = {"error": str(e)}
    except Exception as e:
        logger.error(f"yfinance batch error: {e}")
        return _mock_prices(symbols)

    return results


def get_correlation_matrix(symbols: list[str], period: str = "1y") -> dict[str, Any]:
    """Compute correlation matrix from historical daily returns.

    Returns dict with {matrix: [[float]], symbols: [str], period: str}.
    """
    if not YFINANCE_AVAILABLE:
        return _mock_correlation(symbols)

    try:
        data = yf.download(symbols, period=period, progress=False)
        if "Close" in data.columns.get_level_values(0):
            closes = data["Close"]
        else:
            closes = data  # Single symbol

        returns = closes.pct_change().dropna()
        corr = returns.corr()

        return {
            "matrix": corr.values.tolist(),
            "symbols": list(corr.columns),
            "period": period,
            "data_points": len(returns),
        }
    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}")
        return _mock_correlation(symbols)


def get_portfolio_summary(symbols: list[str]) -> str:
    """Build a markdown summary of portfolio data for the Finance Agent."""
    prices = get_stock_prices(symbols)
    lines = ["## Live Portfolio Data\n"]
    lines.append("| Symbol | Price | Change | Sector |")
    lines.append("|--------|-------|--------|--------|")

    for sym, data in prices.items():
        if "error" in data:
            lines.append(f"| {sym} | Error | — | — |")
            continue
        change_str = f"{data.get('change', 0):+.2f} ({data.get('change_pct', 0):+.1f}%)"
        lines.append(
            f"| {sym} | ${data.get('price', 0):.2f} | {change_str} | {data.get('sector', '—')} |"
        )

    return "\n".join(lines)


def _mock_prices(symbols: list[str]) -> dict[str, Any]:
    """Return mock prices when yfinance is unavailable."""
    import random
    results = {}
    for sym in symbols:
        price = round(random.uniform(50, 500), 2)
        change = round(random.uniform(-5, 5), 2)
        results[sym] = {
            "price": price,
            "change": change,
            "change_pct": round((change / price) * 100, 2),
            "name": f"{sym} (mock)",
            "currency": "USD",
            "mock": True,
        }
    return results


def _mock_correlation(symbols: list[str]) -> dict[str, Any]:
    """Return a mock correlation matrix."""
    import random
    n = len(symbols)
    matrix = [[1.0 if i == j else round(random.uniform(0.2, 0.8), 3)
               for j in range(n)] for i in range(n)]
    return {"matrix": matrix, "symbols": symbols, "period": "1y", "mock": True}
