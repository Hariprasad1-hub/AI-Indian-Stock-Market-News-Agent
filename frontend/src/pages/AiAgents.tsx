import React, { useEffect, useState } from 'react';
import { Bot, ShieldCheck, Activity, Brain, Zap } from 'lucide-react';
import { api } from '../services/api';
import { Agent } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const AiAgents: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const data = await api.getAgents();
        setAgents(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  if (loading) return <LoadingSpinner message="Auditing autonomous agent mesh..." />;

  const AGENT_ICONS: Record<string, React.ElementType> = {
    market_intelligence: Brain,
    market_analyst: Activity,
    trader: Zap,
    risk_manager: ShieldCheck,
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Autonomous AI Agent Architecture
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Four independent agents collaborating through the BAND messaging protocol.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {agents.map((agent) => {
          const Icon = AGENT_ICONS[agent.role] || Bot;
          return (
            <div
              key={agent.id}
              className="glass-panel glass-panel-hover rounded-xl p-6 space-y-4 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="h-10 w-10 rounded-xl bg-navy-800 flex items-center justify-center text-cyan-400 border border-navy-700">
                    <Icon className="h-5 w-5" />
                  </div>
                  <StatusBadge status={agent.status} />
                </div>

                <div>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400 font-bold">
                    Agent #{agent.id} • {agent.role}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-0.5">{agent.name}</h3>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed font-sans">
                  {agent.description || 'Specialized intelligence operative.'}
                </p>
              </div>

              <div className="space-y-2 pt-3 border-t border-navy-800/80">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block font-bold">
                  Core Capabilities
                </span>
                <p className="text-xs font-mono text-slate-300 bg-navy-850 px-3 py-2 rounded-lg border border-navy-800">
                  {agent.capabilities || 'Autonomous reasoning & structured communication.'}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Collaboration Flow Diagram Banner */}
      <div className="glass-panel rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
          Multi-Agent Collaboration Pipeline (BAND Standard)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-center text-xs font-mono">
          <div className="p-3 bg-navy-850 rounded-lg border border-navy-800">
            <span className="text-cyan-400 font-bold block mb-1">1. Intelligence</span>
            <span className="text-slate-400 text-[11px]">BSE/ET Disclosures Normalized</span>
          </div>
          <div className="p-3 bg-navy-850 rounded-lg border border-navy-800">
            <span className="text-cyan-400 font-bold block mb-1">2. Analyst</span>
            <span className="text-slate-400 text-[11px]">Sentiment & Evidence Scored</span>
          </div>
          <div className="p-3 bg-navy-850 rounded-lg border border-navy-800">
            <span className="text-cyan-400 font-bold block mb-1">3. Trader</span>
            <span className="text-slate-400 text-[11px]">Position Planned & Proposed</span>
          </div>
          <div className="p-3 bg-navy-850 rounded-lg border border-navy-800">
            <span className="text-cyan-400 font-bold block mb-1">4. Risk Manager</span>
            <span className="text-slate-400 text-[11px]">Deterministic Safety Gate</span>
          </div>
        </div>
      </div>
    </div>
  );
};
