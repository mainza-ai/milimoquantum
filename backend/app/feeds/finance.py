"""Milimo Quantum — Real-Time Financial Data Feed.

Fetches live ticker and historical data using yahooquery for 
the Finance Agent's portfolio optimization routines.
"""
from __future__ import annotations

import logging
from typing import Any

from yahooquery import Ticker, search

logger = logging.getLogger(__name__)

def get_ticker_data(symbol: str) -> dict[str, Any]:
    """Fetch live data and recent history for a ticker symbol."""
    try:
        t = Ticker(symbol)
        
        # Check if symbol is valid by getting price
        price_data = t.price
        
        if isinstance(price_data, dict) and symbol in price_data and isinstance(price_data[symbol], str):
            # Yahooquery returns a string error message when symbol is invalid
            return {"error": f"Invalid ticker symbol: {symbol}"}
            
        # Get historical data (last 30 days)
        try:
            hist_df = t.history(period="1mo")
            if not hist_df.empty:
                # Reset multi-index if string symbol
                if symbol in hist_df.index:
                    hist_df = hist_df.loc[symbol]
                
                # Convert to dict for JSON serialization, handling timestamps
                hist_df = hist_df.reset_index()
                if "date" in hist_df.columns:
                    hist_df["date"] = hist_df["date"].astype(str)
                history = hist_df.to_dict(orient="records")
            else:
                history = []
        except Exception as e:
            logger.warning(f"Could not fetch history for {symbol}: {e}")
            history = []

        # Extract useful metrics
        summary = t.summary_detail.get(symbol, {})
        if isinstance(summary, str): # Error dict fallback
            summary = {}
            
        financials = t.financial_data.get(symbol, {})
        if isinstance(financials, str):
            financials = {}

        return {
            "symbol": symbol,
            "status": "success",
            "current_price": price_data.get(symbol, {}).get("regularMarketPrice"),
            "currency": price_data.get(symbol, {}).get("currency"),
            "market_cap": summary.get("marketCap"),
            "fifty_two_week_high": summary.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": summary.get("fiftyTwoWeekLow"),
            "operating_margins": financials.get("operatingMargins"),
            "profit_margins": financials.get("profitMargins"),
            "history_30d": history
        }
    except Exception as e:
        logger.error(f"Finance API error for {symbol}: {e}")
        return {"error": str(e)}

def search_symbols(query: str) -> list[dict]:
    """Search for matching ticker symbols."""
    try:
        results = search(query)
        quotes = results.get("quotes", [])
        return [
            {
                "symbol": q.get("symbol"),
                "name": q.get("shortname", q.get("longname", "Unknown")),
                "exchange": q.get("exchange", "Unknown")
            }
            for q in quotes if "symbol" in q
        ][:10]
    except Exception as e:
        logger.error(f"Finance search API error for {query}: {e}")
        # Fallback pseudo-search
        return [{"symbol": query.upper(), "name": "Exact match attempt"}]
