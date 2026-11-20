import re
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import NewsArticle, Stock
from .broker import AgentMessageBroker

# Verified dictionary of major Indian company names and common aliases mapped to NSE ticker symbols
INDIAN_COMPANY_SYMBOLS = {
    "reliance": "RELIANCE",
    "reliance industries": "RELIANCE",
    "tata consultancy": "TCS",
    "tcs": "TCS",
    "infosys": "INFY",
    "infy": "INFY",
    "hdfc bank": "HDFCBANK",
    "hdfc": "HDFCBANK",
    "icici bank": "ICICIBANK",
    "icici": "ICICIBANK",
    "state bank of india": "SBIN",
    "sbi": "SBIN",
    "larsen & toubro": "LT",
    "l&t": "LT",
    "bharti airtel": "BHARTIARTL",
    "airtel": "BHARTIARTL",
    "itc": "ITC",
    "tata motors": "TATAMOTORS",
    "wipro": "WIPRO",
    "maruti": "MARUTI",
    "maruti suzuki": "MARUTI",
    "sun pharma": "SUNPHARMA",
}

class MarketIntelligenceAgent:
    """Agent 1: Market Intelligence Agent.
    Monitors news, normalizes entities to verified NSE symbols, extracts financial facts,
    and publishes structured FINDINGS.
    """
    ROLE = "market_intelligence"

    def __init__(self, session: AsyncSession, broker: AgentMessageBroker):
        self.session = session
        self.broker = broker

    def extract_symbols(self, text: str) -> List[str]:
        """Extract verified Indian stock symbols from article text."""
        lowered = text.lower()
        matched = []
        for name, symbol in INDIAN_COMPANY_SYMBOLS.items():
            pattern = r'\b' + re.escape(name) + r'\b'
            if re.search(pattern, lowered):
                if symbol not in matched:
                    matched.append(symbol)
        return matched

    async def process_article(self, article: NewsArticle, task_id: str, correlation_id: str) -> Dict[str, Any]:
        """Process news article and dispatch structured FINDINGS message to Market Analyst."""
        full_text = f"{article.title} {article.summary or ''} {article.content or ''}"
        detected_symbols = self.extract_symbols(full_text)

        # Extract percentages or monetary figures
        pct_matches = re.findall(r'(\d+(?:\.\d+)?\s*%)', full_text)
        cr_matches = re.findall(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|cr)', full_text, re.IGNORECASE)

        findings = {
            "article_id": article.id,
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "detected_symbols": detected_symbols,
            "extracted_figures": {
                "percentages": pct_matches[:3],
                "crores": cr_matches[:3],
            },
            "uncertainty_flag": len(detected_symbols) == 0,
        }

        # Send structured message to Market Analyst
        await self.broker.send_message(
            sender_role=self.ROLE,
            recipient_role="market_analyst",
            message_type="FINDINGS",
            task_id=task_id,
            correlation_id=correlation_id,
            payload=findings,
        )

        return findings
