from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class MarketQuote:
    symbol: str
    price: Optional[Decimal]
    price_status: str # "LIVE", "STALE", "UNAVAILABLE"
    timestamp: datetime
    exchange: str = "NSE"
    source: str = "SIMULATED_LEDGER"
    metadata: Optional[Dict[str, Any]] = None

class BaseMarketDataProvider(ABC):
    """Abstract interface for Indian equity market data providers (NSE/BSE)."""

    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketQuote:
        """Fetch market quote for a stock symbol."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection to live market data feed is active."""
        pass

class ExternalNSEMarketDataProvider(BaseMarketDataProvider):
    """Production provider interface for external NSE/BSE feeds (e.g. Zerodha Kite, Upstox, NSE Python).
    Honesty Status: Currently NOT CONNECTED. No real live trading API or broker credentials are configured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def is_connected(self) -> bool:
        # Honest check: returns False until valid external market data subscription/key is provided
        return bool(self.api_key)

    async def get_quote(self, symbol: str) -> MarketQuote:
        if not self.is_connected():
            return MarketQuote(
                symbol=symbol,
                price=None,
                price_status="UNAVAILABLE",
                timestamp=datetime.now(timezone.utc),
                source="EXTERNAL_NSE_UNCONNECTED",
                metadata={"error": "Live market data provider is not connected. Requires verified broker/data subscription."},
            )
        # Placeholder for live WebSocket/REST fetch
        raise NotImplementedError("Live external market data adapter is not configured.")
