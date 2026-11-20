import React from 'react';

interface StatusBadgeProps {
  status: string;
  variant?: 'sentiment' | 'execution' | 'risk' | 'price' | 'default';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const norm = (status || '').toUpperCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (['BULLISH', 'APPROVED', 'EXECUTED', 'LIVE', 'WORKING'].includes(norm)) {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (['BEARISH', 'REJECTED', 'FAILED', 'UNAVAILABLE', 'CRITICAL', 'BLOCKED'].includes(norm)) {
    colorClasses = 'bg-coral-500/10 text-coral-400 border-coral-500/30';
  } else if (['PENDING', 'STALE', 'WARNING', 'FLAGGED'].includes(norm)) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (['BUY'].includes(norm)) {
    colorClasses = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  } else if (['SELL'].includes(norm)) {
    colorClasses = 'bg-purple-500/10 text-purple-400 border-purple-500/30';
  } else if (['NEUTRAL', 'HOLD', 'NO_ACTION', 'IDLE'].includes(norm)) {
    colorClasses = 'bg-navy-800 text-slate-400 border-navy-700';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold font-mono tracking-wider border uppercase ${colorClasses}`}
    >
      {status}
    </span>
  );
};
