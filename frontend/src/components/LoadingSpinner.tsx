import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner: React.FC<{ message?: string }> = ({ message = 'Loading live data...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 className="h-8 w-8 text-cyan-400 animate-spin mb-3" />
      <span className="text-xs text-slate-400 font-mono tracking-wider uppercase">
        {message}
      </span>
    </div>
  );
};
