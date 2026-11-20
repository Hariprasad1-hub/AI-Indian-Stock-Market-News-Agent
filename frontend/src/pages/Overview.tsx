import React, { useEffect, useState } from 'react';
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  Bot,
  Activity,
  RefreshCw,
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import { DashboardSummary, Stock } from '../types';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

export const Overview: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumData, stockData] = await Promise.all([
        api.getDashboardSummary(),
        api.getStocks(0, 8),
      ]);
      setSummary(sumData);
      setStocks(stockData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard summary.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) return <LoadingSpinner message="Calculating real-time portfolio metrics..." />;

  // Mock chart points based on real cash and valuation
  const chartData = summary
    ? [
        { time: '09:15', value: 100000 },
        { time: '11:30', value: 99850 },
        { time: '13:00', value: 100120 },
        { time: '14:30', value: 99950 },
        { time: '15:30', value: Number(summary.portfolio_value) || 100000 },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Market Intelligence & Portfolio Overview
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time multi-agent execution telemetry and deterministic paper trading.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3.5 py-2 bg-navy-850 hover:bg-navy-800 text-xs font-mono text-cyan-400 border border-navy-700 rounded-lg transition-all"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Data
        </button>
      </div>

      {error && (
        <div className="p-4 bg-coral-500/10 border border-coral-500/30 rounded-xl text-xs text-coral-300 font-mono">
          {error}
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Portfolio Value"
          value={`₹${Number(summary?.portfolio_value || 100000).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
          })}`}
          subtitle="Virtual Capital + Open Holdings"
          icon={Wallet}
          trend={Number(summary?.total_unrealized_pnl || 0) >= 0 ? 'up' : 'down'}
          trendValue={`₹${Number(summary?.total_unrealized_pnl || 0).toFixed(2)} Unrealized`}
        />
        <StatCard
          title="Available Cash"
          value={`₹${Number(summary?.available_cash || 100000).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
          })}`}
          subtitle="Unallocated Virtual Reserves"
          icon={TrendingUp}
        />
        <StatCard
          title="Realized P&L"
          value={`₹${Number(summary?.total_realized_pnl || 0).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
          })}`}
          subtitle={`${summary?.total_trades || 0} Total Trades Executed`}
          icon={TrendingDown}
          trend={Number(summary?.total_realized_pnl || 0) >= 0 ? 'up' : 'down'}
        />
        <StatCard
          title="Autonomous Agents"
          value={`${summary?.active_agents_count || 4} Active`}
          subtitle={`${summary?.pending_decisions_count || 0} Pending Proposals`}
          icon={Bot}
        />
      </div>

      {/* Main Grid: Performance Chart & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Performance Chart */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                Intraday Portfolio Valuation
              </h3>
              <p className="text-xs text-slate-500">Starting virtual capital: ₹1,00,000</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/20">
              ₹INR Paper Trading
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="valGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} fontStyle="monospace" />
                <YAxis
                  domain={['dataMin - 1000', 'dataMax + 1000']}
                  stroke="#475569"
                  fontSize={11}
                  fontStyle="monospace"
                  tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0b101e',
                    borderColor: '#1f2d4d',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                  }}
                  formatter={(value: any) => [`₹${Number(value).toFixed(2)}`, 'Valuation']}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#00f0ff"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#valGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Recent Activity Feed */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider mb-3">
              Recent Multi-Agent Events
            </h3>
            <div className="space-y-3">
              {summary?.recent_activity && summary.recent_activity.length > 0 ? (
                summary.recent_activity.slice(0, 5).map((act, i) => (
                  <div
                    key={i}
                    className="p-3 bg-navy-850/70 border border-navy-800 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-white text-[11px]">
                        {act.title}
                      </span>
                      <StatusBadge status={act.status} />
                    </div>
                    <p className="text-slate-400 text-[11px] truncate">{act.description}</p>
                    <span className="text-[10px] text-slate-500 font-mono block">
                      {new Date(act.timestamp).toLocaleTimeString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                ))
              ) : (
                <EmptyState
                  title="No Recent Activity"
                  description="Agent proposals and paper trades will appear here as news is processed."
                  icon={Activity}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tracked Indian Stocks Overview */}
      <div className="glass-panel rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              Tracked Equity Instruments (NSE/BSE)
            </h3>
            <p className="text-xs text-slate-500">
              Verified tickers monitored by Market Intelligence Agent.
            </p>
          </div>
        </div>

        {stocks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-navy-850/80 text-slate-400 uppercase text-[10px] border-b border-navy-800">
                <tr>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Company Name</th>
                  <th className="py-2.5 px-3">Exchange</th>
                  <th className="py-2.5 px-3">Sector</th>
                  <th className="py-2.5 px-3">Current Quote</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/60">
                {stocks.map((stock) => (
                  <tr key={stock.id} className="hover:bg-navy-850/40">
                    <td className="py-3 px-3 font-bold text-cyan-400">{stock.symbol}</td>
                    <td className="py-3 px-3 text-slate-300 font-sans text-xs">{stock.name}</td>
                    <td className="py-3 px-3 text-slate-400">{stock.exchange}</td>
                    <td className="py-3 px-3 text-slate-400">{stock.sector || 'General'}</td>
                    <td className="py-3 px-3 font-bold text-white">
                      {stock.current_price
                        ? `₹${Number(stock.current_price).toFixed(2)}`
                        : 'Unavailable'}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={stock.price_status || 'LIVE'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="No Tracked Stocks"
            description="Stocks monitored by the Market Intelligence Agent will appear here."
          />
        )}
      </div>
    </div>
  );
};
