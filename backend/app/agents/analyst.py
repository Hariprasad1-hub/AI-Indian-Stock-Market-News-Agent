from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Stock
from .broker import AgentMessageBroker

BULLISH_KEYWORDS = ["profit", "surges", "growth", "jump", "rally", "rallies", "order win", "dividend", "outperform", "record high"]
BEARISH_KEYWORDS = ["loss", "plunges", "slump", "fraud", "penalty", "investigation", "downgrade", "fall", "decline", "weak"]

class MarketAnalystAgent:
    """Agent 2: Market Analyst Agent.
    Evaluates news evidence, generates sentiment scores (-1.0 to 1.0),
    estimates sector/market impact, and scores analytical confidence.
    """
    ROLE = "market_analyst"

    def __init__(self, session: AsyncSession, broker: AgentMessageBroker):
        self.session = session
        self.broker = broker

    async def analyze_findings(
        self,
        findings: Dict[str, Any],
        task_id: str,
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Analyze findings and dispatch STRUCTURED_ANALYSIS message to Trader."""
        title = findings.get("title", "")
        lowered = title.lower()

        bullish_hits = [w for w in BULLISH_KEYWORDS if w in lowered]
        bearish_hits = [w for w in BEARISH_KEYWORDS if w in lowered]

        if len(bullish_hits) > len(bearish_hits):
            sentiment = "BULLISH"
            sentiment_score = 0.75 + (0.05 * min(len(bullish_hits), 4))
            impact = "HIGH_POSITIVE"
        elif len(bearish_hits) > len(bullish_hits):
            sentiment = "BEARISH"
            sentiment_score = -0.75 - (0.05 * min(len(bearish_hits), 4))
            impact = "HIGH_NEGATIVE"
        else:
            sentiment = "NEUTRAL"
            sentiment_score = 0.0
            impact = "NEUTRAL"

        # Confidence based on entity specificity and figure extraction
        confidence = 0.50
        if findings.get("detected_symbols"):
            confidence += 0.25
        if findings.get("extracted_figures", {}).get("percentages") or findings.get("extracted_figures", {}).get("crores"):
            confidence += 0.15

        confidence = min(round(confidence, 2), 0.95)

        # Primary target symbol
        symbols = findings.get("detected_symbols", [])
        primary_symbol = symbols[0] if symbols else None

        analysis = {
            "article_id": findings.get("article_id"),
            "primary_symbol": primary_symbol,
            "all_symbols": symbols,
            "sentiment": sentiment,
            "sentiment_score": float(sentiment_score),
            "confidence_score": confidence,
            "market_impact": impact,
            "evidence": {
                "bullish_signals": bullish_hits,
                "bearish_signals": bearish_hits,
                "extracted_figures": findings.get("extracted_figures", {}),
            },
        }

        # Send structured analysis to Trader
        await self.broker.send_message(
            sender_role=self.ROLE,
            recipient_role="trader",
            message_type="STRUCTURED_ANALYSIS",
            task_id=task_id,
            correlation_id=correlation_id,
            payload=analysis,
        )

        return analysis
