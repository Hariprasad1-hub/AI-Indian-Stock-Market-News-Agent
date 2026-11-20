import React, { useEffect, useState } from 'react';
import { MessageSquare, Terminal, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { AgentMessage } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

export const AgentActivity: React.FC = () => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');

  const fetchMessages = async () => {
    try {
      setLoading(true);
      const data = await api.getAgentMessages(0, 50, undefined, undefined);
      setMessages(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, [typeFilter]);

  const filteredMessages = typeFilter
    ? messages.filter((m) => m.message_type === typeFilter)
    : messages;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Agent Collaboration & Communication Log
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full audit log of structured BAND protocol messages passing between agents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-navy-850 text-slate-200 text-xs font-mono px-3 py-2 rounded-lg border border-navy-750 focus:outline-none"
          >
            <option value="">All Message Types</option>
            <option value="FINDINGS">FINDINGS</option>
            <option value="STRUCTURED_ANALYSIS">STRUCTURED_ANALYSIS</option>
            <option value="TRADE_PROPOSAL">TRADE_PROPOSAL</option>
            <option value="RISK_ASSESSMENT">RISK_ASSESSMENT</option>
          </select>
          <button
            onClick={fetchMessages}
            className="p-2 bg-navy-850 hover:bg-navy-800 text-cyan-400 border border-navy-750 rounded-lg transition-all"
            title="Refresh Log"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Retrieving structured agent collaboration messages..." />
      ) : filteredMessages.length > 0 ? (
        <div className="space-y-4">
          {filteredMessages.map((msg) => {
            let parsedPayload: any = null;
            try {
              parsedPayload = JSON.parse(msg.payload);
            } catch {
              parsedPayload = msg.payload;
            }

            return (
              <div
                key={msg.id}
                className="glass-panel glass-panel-hover rounded-xl p-5 space-y-3 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-navy-800/80 pb-3">
                  <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                    <span className="font-bold text-cyan-400">
                      {msg.sender_name || `Agent #${msg.sender_id}`}
                    </span>
                    <span className="text-slate-500">➔</span>
                    <span className="font-bold text-white">
                      {msg.recipient_name || `Agent #${msg.recipient_id}`}
                    </span>
                    <span className="text-slate-500">|</span>
                    <StatusBadge status={msg.message_type} />
                  </div>
                  <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500">
                    <span>Task: {msg.task_id || 'N/A'}</span>
                    <span>
                      {new Date(msg.timestamp).toLocaleTimeString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })} IST
                    </span>
                  </div>
                </div>

                {/* Structured JSON Payload display */}
                <div className="bg-navy-950 p-3.5 rounded-lg border border-navy-850 overflow-x-auto text-[11px] font-mono text-slate-300">
                  <div className="flex items-center gap-1.5 text-slate-500 text-[10px] mb-2 uppercase tracking-widest font-bold">
                    <Terminal className="h-3 w-3" />
                    <span>BAND Protocol Payload (Correlation: {msg.correlation_id || 'N/A'})</span>
                  </div>
                  <pre className="text-cyan-300">
                    {typeof parsedPayload === 'object'
                      ? JSON.stringify(parsedPayload, null, 2)
                      : String(parsedPayload)}
                  </pre>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          title="No Agent Messages Logged"
          description="Messages exchanged between Intelligence, Analyst, Trader and Risk Manager will appear here."
          icon={MessageSquare}
        />
      )}
    </div>
  );
};
