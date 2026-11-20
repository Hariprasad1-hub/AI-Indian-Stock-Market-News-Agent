import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    String,
    Text,
    Numeric,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

class UTCDateTime(TypeDecorator):
    """Ensures datetime is always UTC timezone-aware on SQLite and PostgreSQL."""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)

class NewsArticle(Base):
    """Normalized financial news article ingested from RSS/n8n."""
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True) # BULLISH, BEARISH, NEUTRAL
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True) # -1.0000 to +1.0000
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    # Relationships
    decisions: Mapped[List["TradingDecision"]] = relationship("TradingDecision", back_populates="article")

    def __repr__(self) -> str:
        return f"<NewsArticle id={self.id} title={self.title[:30]!r} sentiment={self.sentiment}>"


class Stock(Base):
    """Monitored stock instrument (e.g., NSE/BSE tickers)."""
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), default="NSE", nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    price_status: Mapped[str] = mapped_column(String(20), default="LIVE", nullable=False) # LIVE, STALE, UNAVAILABLE
    price_updated_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, default=utc_now, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    holdings: Mapped[List["Holding"]] = relationship("Holding", back_populates="stock")
    transactions: Mapped[List["TradeTransaction"]] = relationship("TradeTransaction", back_populates="stock")
    decisions: Mapped[List["TradingDecision"]] = relationship("TradingDecision", back_populates="stock")

    def __repr__(self) -> str:
        return f"<Stock symbol={self.symbol} price={self.current_price} status={self.price_status}>"


class Agent(Base):
    """Independent AI agent profile and execution state."""
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # market_intelligence, market_analyst, trader, risk_manager
    status: Mapped[str] = mapped_column(String(30), default="IDLE", nullable=False) # IDLE, WORKING, ERROR, OFFLINE
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    capabilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    sent_messages: Mapped[List["AgentMessage"]] = relationship(
        "AgentMessage",
        foreign_keys="[AgentMessage.sender_id]",
        back_populates="sender",
    )
    received_messages: Mapped[List["AgentMessage"]] = relationship(
        "AgentMessage",
        foreign_keys="[AgentMessage.recipient_id]",
        back_populates="recipient",
    )
    decisions: Mapped[List["TradingDecision"]] = relationship("TradingDecision", back_populates="agent")

    def __repr__(self) -> str:
        return f"<Agent id={self.id} name={self.name} status={self.status}>"


class AgentMessage(Base):
    """Structured message for genuine agent-to-agent collaboration (BAND protocol)."""
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # TASK_DELEGATION, FINDINGS, STRUCTURED_ANALYSIS, TRADE_PROPOSAL, RISK_ASSESSMENT, FEEDBACK
    task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False) # Structured JSON payload
    status: Mapped[str] = mapped_column(String(20), default="DELIVERED", nullable=False) # PENDING, DELIVERED, PROCESSED, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    sender: Mapped["Agent"] = relationship("Agent", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient: Mapped["Agent"] = relationship("Agent", foreign_keys=[recipient_id], back_populates="received_messages")

    def __repr__(self) -> str:
        return f"<AgentMessage id={self.message_id} type={self.message_type} status={self.status}>"


class TradingDecision(Base):
    """Trade proposal generated by Trader Agent and evaluated by Risk Manager."""
    __tablename__ = "trading_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # BUY, SELL, HOLD, NO_ACTION
    stock_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("stocks.id"), nullable=True, index=True)
    agent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    article_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("news_articles.id"), nullable=True, index=True)
    proposed_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    proposed_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True) # 0.0000 to 1.0000
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True) # PENDING, APPROVED, REJECTED, EXECUTED
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    # Relationships
    stock: Mapped[Optional["Stock"]] = relationship("Stock", back_populates="decisions")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="decisions")
    article: Mapped[Optional["NewsArticle"]] = relationship("NewsArticle", back_populates="decisions")
    risk_events: Mapped[List["RiskEvent"]] = relationship("RiskEvent", back_populates="decision")
    transactions: Mapped[List["TradeTransaction"]] = relationship("TradeTransaction", back_populates="decision")

    def __repr__(self) -> str:
        return f"<TradingDecision id={self.id} type={self.decision_type} status={self.status}>"


class Portfolio(Base):
    """Simulated virtual portfolio."""
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), default="Default Virtual Portfolio", nullable=False)
    initial_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("100000.00"), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("100000.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    holdings: Mapped[List["Holding"]] = relationship("Holding", back_populates="portfolio")
    transactions: Mapped[List["TradeTransaction"]] = relationship("TradeTransaction", back_populates="portfolio")

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} cash={self.cash_balance}>"


class Holding(Base):
    """Current stock holdings within a portfolio."""
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    stock_id: Mapped[int] = mapped_column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_buy_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="holdings")

    def __repr__(self) -> str:
        return f"<Holding portfolio={self.portfolio_id} stock={self.stock_id} qty={self.quantity}>"


class TradeTransaction(Base):
    """Executed paper-trading order record."""
    __tablename__ = "trade_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    stock_id: Mapped[int] = mapped_column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    decision_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trading_decisions.id"), nullable=True, index=True)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True) # BUY, SELL
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="transactions")
    decision: Mapped[Optional["TradingDecision"]] = relationship("TradingDecision", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<TradeTransaction id={self.id} type={self.transaction_type} qty={self.quantity} price={self.execution_price}>"


class RiskEvent(Base):
    """Risk assessment rule evaluations and compliance events."""
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trading_decisions.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # CAPITAL_LIMIT, POSITION_LIMIT, CONCENTRATION_LIMIT, DAILY_LOSS_LIMIT, PRICE_STALENESS
    severity: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False) # INFO, WARNING, CRITICAL, BLOCKED
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # APPROVED, REJECTED, FLAGGED
    checked_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    decision: Mapped[Optional["TradingDecision"]] = relationship("TradingDecision", back_populates="risk_events")

    def __repr__(self) -> str:
        return f"<RiskEvent id={self.id} type={self.event_type} status={self.status}>"
