export interface DashboardSummary {
  portfolio_value: string;
  available_cash: string;
  invested_value: string;
  total_realized_pnl: string;
  total_unrealized_pnl: string;
  total_trades: number;
  active_agents_count: number;
  total_news_count: number;
  pending_decisions_count: number;
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  type: string;
  id: number;
  title: string;
  description: string;
  status: string;
  timestamp: string;
}

export interface NewsArticle {
  id: number;
  title: string;
  content: string | null;
  summary: string | null;
  source: string;
  url: string;
  published_at: string | null;
  sentiment: string | null;
  sentiment_score: string | number | null;
  created_at: string;
}

export interface Stock {
  id: number;
  symbol: string;
  name: string;
  exchange: string;
  sector: string | null;
  current_price: string | number | null;
  price_status: 'LIVE' | 'STALE' | 'UNAVAILABLE';
  price_updated_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: number;
  name: string;
  role: string;
  status: 'IDLE' | 'WORKING' | 'ERROR' | 'OFFLINE';
  description: string | null;
  capabilities: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentMessage {
  id: number;
  message_id: string;
  sender_id: number;
  recipient_id: number;
  sender_name?: string | null;
  recipient_name?: string | null;
  message_type: string;
  task_id: string | null;
  correlation_id: string | null;
  payload: string;
  status: string;
  error_message?: string | null;
  timestamp: string;
}

export interface TradingDecision {
  id: number;
  decision_type: 'BUY' | 'SELL' | 'HOLD' | 'NO_ACTION';
  stock_id: number | null;
  stock_symbol?: string | null;
  agent_id: number | null;
  agent_name?: string | null;
  article_id: number | null;
  proposed_quantity: number;
  proposed_price: string | number | null;
  confidence_score: string | number | null;
  reasoning: string | null;
  evidence: string | null;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXECUTED';
  rejection_reason?: string | null;
  created_at: string;
}

export interface Holding {
  id: number;
  portfolio_id: number;
  stock_id: number;
  stock_symbol: string;
  quantity: number;
  average_buy_price: string;
  current_price: string;
  invested_amount: string;
  current_value: string;
  unrealized_pnl: string;
  realized_pnl: string;
  updated_at: string;
}

export interface Portfolio {
  id: number;
  name: string;
  initial_cash: string;
  cash_balance: string;
  invested_value: string;
  total_portfolio_value: string;
  unrealized_pnl: string;
  realized_pnl: string;
  currency: string;
  holdings_count: number;
  holdings: Holding[];
  created_at: string;
  updated_at: string;
}

export interface TradeTransaction {
  id: number;
  portfolio_id: number;
  stock_id: number;
  stock_symbol: string;
  decision_id: number | null;
  transaction_type: 'BUY' | 'SELL';
  quantity: number;
  execution_price: string;
  total_amount: string;
  fee: string;
  executed_at: string;
}

export interface RiskEvent {
  id: number;
  decision_id: number | null;
  event_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'BLOCKED';
  description: string;
  status: 'APPROVED' | 'REJECTED' | 'FLAGGED';
  checked_at: string;
}

export interface SponsorIntegration {
  name: string;
  status: 'CONNECTED' | 'NOT CONNECTED' | 'NOT IMPLEMENTED';
  details: string;
  auth_configured: boolean;
}

export interface AppStatus {
  project: string;
  database_engine: string;
  risk_limits: {
    max_position_pct: number;
    max_sector_pct: number;
    price_max_staleness_minutes: number;
    max_daily_loss_pct: number;
    transaction_fee_pct: number;
    duplicate_proposal_window_minutes: number;
  };
  integrations: Record<string, SponsorIntegration>;
}
