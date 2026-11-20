import {
  DashboardSummary,
  NewsArticle,
  Stock,
  Agent,
  AgentMessage,
  TradingDecision,
  Portfolio,
  TradeTransaction,
  RiskEvent,
  AppStatus,
  SponsorIntegration,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Health
  getHealth: () => fetchJson<{ status: string; project: string; db_connected: boolean }>('/health'),

  // Dashboard Summary
  getDashboardSummary: () => fetchJson<DashboardSummary>('/api/dashboard/summary'),

  // News
  getNews: (skip = 0, limit = 20, source?: string, sentiment?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (source) params.append('source', source);
    if (sentiment) params.append('sentiment', sentiment);
    return fetchJson<NewsArticle[]>(`/api/news?${params.toString()}`);
  },

  // Stocks
  getStocks: (skip = 0, limit = 50, symbol?: string, sector?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (symbol) params.append('symbol', symbol);
    if (sector) params.append('sector', sector);
    return fetchJson<Stock[]>(`/api/stocks?${params.toString()}`);
  },

  // Agents
  getAgents: () => fetchJson<Agent[]>('/api/agents'),

  // Agent Messages
  getAgentMessages: (skip = 0, limit = 50, taskId?: string, correlationId?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (taskId) params.append('task_id', taskId);
    if (correlationId) params.append('correlation_id', correlationId);
    return fetchJson<AgentMessage[]>(`/api/agents/messages?${params.toString()}`);
  },

  // Trading Decisions
  getDecisions: (skip = 0, limit = 50, decisionType?: string, status?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (decisionType) params.append('decision_type', decisionType);
    if (status) params.append('status', status);
    return fetchJson<TradingDecision[]>(`/api/decisions?${params.toString()}`);
  },

  // Portfolio
  getPortfolio: () => fetchJson<Portfolio>('/api/portfolio'),

  // Transactions
  getTransactions: (skip = 0, limit = 50, transactionType?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (transactionType) params.append('transaction_type', transactionType);
    return fetchJson<TradeTransaction[]>(`/api/transactions?${params.toString()}`);
  },

  // Risk Events
  getRiskEvents: (skip = 0, limit = 50, status?: string, severity?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    return fetchJson<RiskEvent[]>(`/api/risk/events?${params.toString()}`);
  },

  // Settings & Integrations
  getAppStatus: () => fetchJson<AppStatus>('/api/settings/status'),
  getIntegrations: () => fetchJson<Record<string, SponsorIntegration>>('/api/settings/integrations'),
};
