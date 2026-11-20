import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
}) => {
  return (
    <div className="glass-panel glass-panel-hover rounded-xl p-5 transition-all">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
          {title}
        </span>
        <div className="h-8 w-8 rounded-lg bg-navy-800 flex items-center justify-center text-cyan-400">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        {trendValue && (
          <span
            className={`text-xs font-semibold font-mono ${
              trend === 'up'
                ? 'text-emerald-400'
                : trend === 'down'
                ? 'text-coral-400'
                : 'text-slate-400'
            }`}
          >
            {trend === 'up' ? '+' : ''}
            {trendValue}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
};
