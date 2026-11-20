import React, { useEffect, useState } from 'react';
import { History, Layers, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { Portfolio, TradeTransaction } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

export const PaperTrading: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [transactions, setTransactions] = useState<TradeTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [portData, txData] = await Promise.all([
        api.getPortfolio(),
        api.getTransactions(0, 50),
      ]);
      setPortfolio(portData);
      setTransactions(txData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) return <LoadingSpinner message="Calculating virtual portfolio holdings & transactions..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Simulated Paper-Trading Execution Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Initial virtual capital ₹1,00,000. Verified weighted-average cost accounting and zero real-money risk.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3.5 py-2 bg-navy-850 hover:bg-navy-800 text-xs font-mono text-cyan-400 border border-navy-700 rounded-lg transition-all"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Ledger
        </button>
      </div>

      {/* Capital Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-panel rounded-xl p-5 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Available Cash Balance</span>
          <div className="text-2xl font-bold font-mono text-white">
            ₹{Number(portfolio?.cash_balance || 100000).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">Starting seed: ₹1,00,000.00</p>
        </div>
        <div className="glass-panel rounded-xl p-5 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Invested Value</span>
          <div className="text-2xl font-bold font-mono text-cyan-400">
            ₹{Number(portfolio?.invested_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">{portfolio?.holdings_count || 0} Open Positions</p>
        </div>
        <div className="glass-panel rounded-xl p-5 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Realized Gain/Loss</span>
          <div
            className={`text-2xl font-bold font-mono ${
              Number(portfolio?.realized_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-coral-400'
            }`}
          >
            {Number(portfolio?.realized_pnl || 0) >= 0 ? '+' : ''}
            ₹{Number(portfolio?.realized_pnl || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">Net of 0.1% transaction fees</p>
        </div>
      </div>

      {/* Holdings Section */}
      <div className="glass-panel rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-cyan-400" />
          <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
            Open Portfolio Holdings
          </h3>
        </div>

        {portfolio?.holdings && portfolio.holdings.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-navy-850/80 text-slate-400 uppercase text-[10px] border-b border-navy-800">
                <tr>
                  <th className="py-2.5 px-3">Stock Symbol</th>
                  <th className="py-2.5 px-3">Quantity</th>
                  <th className="py-2.5 px-3">Avg Buy Price</th>
                  <th className="py-2.5 px-3">Current Price</th>
                  <th className="py-2.5 px-3">Total Value</th>
                  <th className="py-2.5 px-3">Unrealized P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/60">
                {portfolio.holdings.map((h) => {
                  const unpnl = Number(h.unrealized_pnl);
                  return (
                    <tr key={h.id} className="hover:bg-navy-850/40">
                      <td className="py-3 px-3 font-bold text-cyan-400">{h.stock_symbol}</td>
                      <td className="py-3 px-3 text-white font-bold">{h.quantity}</td>
                      <td className="py-3 px-3 text-slate-300">₹{Number(h.average_buy_price).toFixed(2)}</td>
                      <td className="py-3 px-3 text-slate-300">₹{Number(h.current_price).toFixed(2)}</td>
                      <td className="py-3 px-3 font-bold text-white">₹{Number(h.current_value).toFixed(2)}</td>
                      <td
                        className={`py-3 px-3 font-bold ${
                          unpnl >= 0 ? 'text-emerald-400' : 'text-coral-400'
                        }`}
                      >
                        {unpnl >= 0 ? '+' : ''}₹{unpnl.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="Zero Open Positions"
            description="Approved buy proposals executed by the paper-trading engine will populate here."
            icon={Layers}
          />
        )}
      </div>

      {/* Transaction History Section */}
      <div className="glass-panel rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-cyan-400" />
          <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
            Executed Transaction History
          </h3>
        </div>

        {transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-navy-850/80 text-slate-400 uppercase text-[10px] border-b border-navy-800">
                <tr>
                  <th className="py-2.5 px-3">TX ID</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Quantity</th>
                  <th className="py-2.5 px-3">Execution Price</th>
                  <th className="py-2.5 px-3">Total Amount</th>
                  <th className="py-2.5 px-3">Fee (0.1%)</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/60">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-navy-850/40">
                    <td className="py-3 px-3 text-slate-500">#{tx.id}</td>
                    <td className="py-3 px-3">
                      <StatusBadge status={tx.transaction_type} />
                    </td>
                    <td className="py-3 px-3 font-bold text-white">{tx.stock_symbol}</td>
                    <td className="py-3 px-3 text-slate-300">{tx.quantity}</td>
                    <td className="py-3 px-3 text-slate-300">₹{Number(tx.execution_price).toFixed(2)}</td>
                    <td className="py-3 px-3 font-bold text-white">₹{Number(tx.total_amount).toFixed(2)}</td>
                    <td className="py-3 px-3 text-slate-400">₹{Number(tx.fee).toFixed(2)}</td>
                    <td className="py-3 px-3 text-slate-500 text-[11px]">
                      {new Date(tx.executed_at).toLocaleString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        dateStyle: 'short',
                        timeStyle: 'medium',
                      })} IST
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="No Executed Transactions"
            description="Only approved risk-compliant decisions enter the execution engine."
            icon={History}
          />
        )}
      </div>
    </div>
  );
};
