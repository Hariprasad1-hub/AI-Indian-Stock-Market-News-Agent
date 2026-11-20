from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field

class NewsArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    source: str
    url: str
    published_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[Decimal] = None

class NewsArticleCreate(NewsArticleBase):
    raw_payload: Optional[str] = None

class NewsArticleOut(NewsArticleBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StockBase(BaseModel):
    symbol: str
    name: str
    exchange: str = "NSE"
    sector: Optional[str] = None
    current_price: Optional[Decimal] = None
    price_status: str = "LIVE" # LIVE, STALE, UNAVAILABLE
    price_updated_at: Optional[datetime] = None
    is_active: bool = True

class StockCreate(StockBase):
    pass

class StockOut(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AgentBase(BaseModel):
    name: str
    role: str
    status: str = "IDLE"
    description: Optional[str] = None
    capabilities: Optional[str] = None

class AgentOut(AgentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AgentMessageBase(BaseModel):
    sender_id: int
    recipient_id: int
    message_type: str
    task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    payload: str
    status: str = "DELIVERED"
    error_message: Optional[str] = None

class AgentMessageOut(AgentMessageBase):
    id: int
    message_id: str
    sender_name: Optional[str] = None
    recipient_name: Optional[str] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class TradingDecisionBase(BaseModel):
    decision_type: str # BUY, SELL, HOLD, NO_ACTION
    stock_id: Optional[int] = None
    agent_id: Optional[int] = None
    article_id: Optional[int] = None
    proposed_quantity: int = 0
    proposed_price: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    reasoning: Optional[str] = None
    evidence: Optional[str] = None

class TradingDecisionOut(TradingDecisionBase):
    id: int
    status: str # PENDING, APPROVED, REJECTED, EXECUTED
    rejection_reason: Optional[str] = None
    stock_symbol: Optional[str] = None
    agent_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class HoldingOut(BaseModel):
    id: int
    portfolio_id: int
    stock_id: int
    stock_symbol: str
    quantity: int
    average_buy_price: Decimal
    current_price: Decimal
    invested_amount: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PortfolioOut(BaseModel):
    id: int
    name: str
    initial_cash: Decimal
    cash_balance: Decimal
    invested_value: Decimal
    total_portfolio_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    currency: str
    holdings_count: int
    holdings: List[HoldingOut] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TradeTransactionOut(BaseModel):
    id: int
    portfolio_id: int
    stock_id: int
    stock_symbol: str
    decision_id: Optional[int] = None
    transaction_type: str
    quantity: int
    execution_price: Decimal
    total_amount: Decimal
    fee: Decimal
    executed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RiskEventOut(BaseModel):
    id: int
    decision_id: Optional[int] = None
    event_type: str
    severity: str
    description: str
    status: str
    checked_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ActivityItem(BaseModel):
    type: str # TRANSACTION, DECISION, RISK, NEWS
    id: int
    title: str
    description: str
    status: str
    timestamp: datetime

class DashboardSummaryOut(BaseModel):
    portfolio_value: Decimal
    available_cash: Decimal
    invested_value: Decimal
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_trades: int
    active_agents_count: int
    total_news_count: int
    pending_decisions_count: int
    recent_activity: List[ActivityItem] = []
