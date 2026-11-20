import React, { useEffect, useState } from 'react';
import { Activity, WifiOff, Clock } from 'lucide-react';
import { api } from '../services/api';

export const Navbar: React.FC = () => {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        setBackendOk(res.status === 'ok' && res.db_connected);
      } catch {
        setBackendOk(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);

    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        }) + ' IST'
      );
    };
    updateTime();
    const clockInterval = setInterval(updateTime, 1000);

    return () => {
      clearInterval(interval);
      clearInterval(clockInterval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-navy-800 bg-navy-900/90 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between px-6">
      {/* Brand & Tagline */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="h-5 w-5 text-black stroke-[2.5]" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              TRADEMIND <span className="text-cyan-400">AI</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium hidden sm:block">
              Four Agents. One Intelligent Market.
            </p>
          </div>
        </div>
      </div>

      {/* Real-time status indicators */}
      <div className="flex items-center gap-5 text-xs font-mono">
        <div className="flex items-center gap-1.5 text-slate-300 bg-navy-850 px-3 py-1.5 rounded-full border border-navy-800">
          <Clock className="h-3.5 w-3.5 text-cyan-400" />
          <span>{timeStr || 'Loading clock...'}</span>
        </div>

        <div className="flex items-center gap-2 bg-navy-850 px-3 py-1.5 rounded-full border border-navy-800">
          {backendOk === true ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-emerald-400 font-medium">Backend Live (8000)</span>
            </>
          ) : backendOk === false ? (
            <>
              <WifiOff className="h-3.5 w-3.5 text-coral-400" />
              <span className="text-coral-400 font-medium">Backend Offline</span>
            </>
          ) : (
            <span className="text-slate-400">Connecting...</span>
          )}
        </div>
      </div>
    </header>
  );
};
