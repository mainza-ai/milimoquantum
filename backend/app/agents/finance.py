"""Milimo Quantum — Finance Agent Wrapper.

Provides an async interface to the financial data feed.
"""
from __future__ import annotations

import anyio
from app.feeds.finance import get_ticker_data


async def get_market_sentiment(symbol: str) -> dict:
    """Fetch market data for a symbol (async wrapper)."""
    # Map 'sentiment' request to ticker data for now
    data = await anyio.to_thread.run_sync(get_ticker_data, symbol)
    return data
