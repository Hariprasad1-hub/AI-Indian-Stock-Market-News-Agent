import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AppStatus, SponsorIntegration } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import {
  Settings as SettingsIcon,
  Database,
  ShieldAlert,
  Layers,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Server,
  Lock
} from 'lucide-react';

export const Settings: React.FC = () => {
  const [appStatus, setAppStatus] = useState<AppStatus | null>(null);
  const [integrations, setIntegrations] = useState<Record<string, SponsorIntegration>>({});
  const [health, setHealth] = useState<{ status: string; project: string; db_connected: boolean } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [statusRes, integRes, healthRes] = await Promise.all([
        api.getAppStatus(),
        api.getIntegrations(),
        api.getHealth(),
      ]);
      setAppStatus(statusRes);
      setIntegrations(integRes);
      setHealth(healthRes);
    } catch (err: any) {
      console.error('Error fetching settings:', err);
      setError(err.message || 'Failed to load system settings');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return <LoadingSpinner message="Loading system configuration & integrations..." />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <SettingsIcon className="w-7 h-7 text-cyan-400" />
            System Settings & Integrations
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            System health, database engine, risk control policies, and sponsor integration status.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-sm font-medium border border-slate-700 transition self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Status
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={handleRefresh} className="underline text-xs hover:text-white">Retry</button>
        </div>
      )}

      {/* Backend & Database Health */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Application State</span>
            <Server className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <StatusBadge status={health?.status === 'ok' ? 'ACTIVE' : 'ERROR'} />
            <span className="text-white font-semibold text-lg">{health?.project || 'TRADEMIND AI'}</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            FastAPI 0.115 backend running with async event loop.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Database Engine</span>
            <Database className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <StatusBadge status={health?.db_connected ? 'SUCCESS' : 'ERROR'} />
            <span className="text-white font-semibold text-lg">
              {appStatus?.database_engine ? appStatus.database_engine.toUpperCase() : 'AIOSQLITE'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            SQLAlchemy 2.x async ORM with Alembic schema versioning.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Environment Mode</span>
            <Lock className="w-5 h-5 text-amber-400" />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              PAPER TRADING ONLY
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Zero real-money risk. Strict Python Decimal financial math.
          </p>
        </div>
      </div>

      {/* Sponsor Integrations Audit */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Sponsor & Ecosystem Integrations</h2>
        </div>
        <p className="text-xs text-slate-400 mb-6">
          Honest real-time status of all hackathon partner technologies and external protocols.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(integrations).map(([key, item]) => {
            const isConnected = item.status === 'CONNECTED';
            return (
              <div
                key={key}
                className={`p-4 rounded-xl border transition ${
                  isConnected
                    ? 'bg-slate-950/60 border-slate-800 hover:border-emerald-500/30'
                    : 'bg-slate-950/40 border-slate-800/60 opacity-80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-white text-sm">{item.name || key}</span>
                  {isConnected ? (
                    <span className="flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3" /> CONNECTED
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                      <XCircle className="w-3 h-3" /> NOT CONNECTED
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {item.details}
                </p>
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Authentication</span>
                  <span className={item.auth_configured ? 'text-emerald-400 font-medium' : 'text-slate-400'}>
                    {item.auth_configured ? 'Configured' : 'Missing / Optional'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Deterministic Risk Limits Configuration */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h2 className="text-lg font-semibold text-white">Deterministic Risk Policy Limits</h2>
        </div>
        <p className="text-xs text-slate-400 mb-6">
          Hard-coded safeguards enforced by the Python Risk Engine before any paper trade can execute.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Max Single Position Exposure</div>
            <div className="text-2xl font-bold text-white mt-1">
              {appStatus?.risk_limits?.max_position_pct ? `${appStatus.risk_limits.max_position_pct * 100}%` : '20%'}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Maximum allocation allowed for any single stock holding.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Max Sector Exposure</div>
            <div className="text-2xl font-bold text-white mt-1">
              {appStatus?.risk_limits?.max_sector_pct ? `${appStatus.risk_limits.max_sector_pct * 100}%` : '35%'}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Maximum allocation allowed across a single industry sector.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Price Max Staleness</div>
            <div className="text-2xl font-bold text-white mt-1">
              {appStatus?.risk_limits?.price_max_staleness_minutes ?? 15} mins
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Quotes older than 15 mins are marked STALE and rejected.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Max Daily Portfolio Loss</div>
            <div className="text-2xl font-bold text-white mt-1">
              {appStatus?.risk_limits?.max_daily_loss_pct ? `${appStatus.risk_limits.max_daily_loss_pct * 100}%` : '5%'}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Circuit breaker triggered if unrealized daily loss exceeds 5%.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Simulated Transaction Fee</div>
            <div className="text-2xl font-bold text-white mt-1">
              {appStatus?.risk_limits?.transaction_fee_pct ? `${appStatus.risk_limits.transaction_fee_pct * 100}%` : '0.1%'}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Slippage and brokerage commission deducted from cash.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Duplicate Proposal Window</div>
            <div className="text-2xl font-bold text-white mt-1">
              {appStatus?.risk_limits?.duplicate_proposal_window_minutes ?? 60} mins
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Prevents duplicate decision proposals for identical stock/action.
            </p>
          </div>
        </div>
      </div>

      {/* System Specifications & Architecture */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Architecture & Technology Stack</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/50">
            <span className="text-slate-400 block font-medium">Frontend Framework</span>
            <span className="text-white font-semibold mt-1 block">React 18 + Vite + TypeScript</span>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/50">
            <span className="text-slate-400 block font-medium">Styling & Icons</span>
            <span className="text-white font-semibold mt-1 block">Tailwind CSS + Lucide Icons</span>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/50">
            <span className="text-slate-400 block font-medium">Backend Framework</span>
            <span className="text-white font-semibold mt-1 block">FastAPI (Async Python 3.14)</span>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/50">
            <span className="text-slate-400 block font-medium">Financial Arithmetic</span>
            <span className="text-emerald-400 font-semibold mt-1 block">Python decimal.Decimal (Fixed-Point)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
