import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { RiskEvent } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

export const RiskManagement: React.FC = () => {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchRiskEvents = async () => {
    try {
      setLoading(true);
      const data = await api.getRiskEvents(0, 50, statusFilter || undefined);
      setEvents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskEvents();
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Deterministic Risk Engine & Compliance
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Strict Python validation rules preventing unauthorized portfolio exposure or capital loss.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-navy-850 text-slate-200 text-xs font-mono px-3 py-2 rounded-lg border border-navy-750 focus:outline-none"
          >
            <option value="">All Risk Evaluations</option>
            <option value="APPROVED">APPROVED Only</option>
            <option value="REJECTED">REJECTED Only</option>
          </select>
          <button
            onClick={fetchRiskEvents}
            className="p-2 bg-navy-850 hover:bg-navy-800 text-cyan-400 border border-navy-750 rounded-lg transition-all"
            title="Refresh Risk Events"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Deterministic Guardrails Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel rounded-xl p-4 space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
            RULE 1: POSITION LIMIT
          </span>
          <div className="text-xl font-bold font-mono text-cyan-400">Max 20.0%</div>
          <p className="text-[11px] text-slate-400">Cap on single stock capital allocation.</p>
        </div>
        <div className="glass-panel rounded-xl p-4 space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
            RULE 2: SECTOR EXPOSURE
          </span>
          <div className="text-xl font-bold font-mono text-cyan-400">Max 35.0%</div>
          <p className="text-[11px] text-slate-400">Concentration threshold per sector.</p>
        </div>
        <div className="glass-panel rounded-xl p-4 space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
            RULE 3: STALENESS CUTOFF
          </span>
          <div className="text-xl font-bold font-mono text-cyan-400">15 Minutes</div>
          <p className="text-[11px] text-slate-400">Stale market quotes automatically rejected.</p>
        </div>
        <div className="glass-panel rounded-xl p-4 space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
            RULE 4: SHORT SELLING
          </span>
          <div className="text-xl font-bold font-mono text-coral-400">STRICTLY PROHIBITED</div>
          <p className="text-[11px] text-slate-400">No unhedged short positions permitted.</p>
        </div>
      </div>

      {/* Risk Events Audit Table */}
      <div className="glass-panel rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
          Risk Assessment Audit Ledger
        </h3>

        {loading ? (
          <LoadingSpinner message="Auditing compliance decisions..." />
        ) : events.length > 0 ? (
          <div className="space-y-3">
            {events.map((ev) => (
              <div
                key={ev.id}
                className={`p-4 rounded-xl border text-xs space-y-2 transition-all ${
                  ev.status === 'APPROVED'
                    ? 'bg-emerald-500/5 border-emerald-500/20'
                    : 'bg-coral-500/5 border-coral-500/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {ev.status === 'APPROVED' ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <AlertOctagon className="h-4 w-4 text-coral-400" />
                    )}
                    <span className="font-mono font-bold text-white">
                      Event #{ev.id} • {ev.event_type}
                    </span>
                  </div>
                  <StatusBadge status={ev.status} />
                </div>

                <p className="text-slate-300 font-mono text-[11px] leading-relaxed">
                  {ev.description}
                </p>

                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 border-t border-navy-800/40 pt-2">
                  <span>Decision Reference: #{ev.decision_id || 'N/A'}</span>
                  <span>
                    {new Date(ev.checked_at).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      dateStyle: 'medium',
                      timeStyle: 'medium',
                    })} IST
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No Risk Events Logged"
            description="Compliance checks triggered by proposals will appear here."
            icon={ShieldCheck}
          />
        )}
      </div>
    </div>
  );
};
