import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Newspaper,
  Bot,
  Compass,
  ShieldAlert,
  CandlestickChart,
  GitBranch,
  Settings,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'Market Intelligence', path: '/intelligence', icon: Newspaper },
  { name: 'AI Agents', path: '/agents', icon: Bot },
  { name: 'Trading Decisions', path: '/decisions', icon: Compass },
  { name: 'Risk Management', path: '/risk', icon: ShieldAlert },
  { name: 'Paper Trading', path: '/paper-trading', icon: CandlestickChart },
  { name: 'Agent Activity', path: '/activity', icon: GitBranch },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-navy-800 bg-navy-900/60 backdrop-blur-sm min-h-[calc(100vh-4rem)] flex flex-col justify-between p-4">
      <nav className="space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
          Intelligence & Trading
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-navy-850'
                }`
              }
            >
              <Icon className="h-4 w-4 stroke-[2]" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 bg-navy-850/80 rounded-xl border border-navy-800 text-xs text-slate-400 space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px] text-slate-400">
          <span>PORTFOLIO SEED</span>
          <span className="text-emerald-400 font-bold">₹1,00,000</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-500">
          Deterministic execution engine with zero real-money risk.
        </p>
      </div>
    </aside>
  );
};
