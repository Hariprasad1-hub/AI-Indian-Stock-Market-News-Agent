import React from 'react';
import { Database } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ElementType;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Database,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-navy-800 rounded-xl bg-navy-900/30">
      <div className="h-12 w-12 rounded-full bg-navy-850 flex items-center justify-center text-slate-500 mb-3 border border-navy-800">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-sm font-bold text-slate-300 font-mono">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm mt-1 leading-relaxed">
        {description}
      </p>
    </div>
  );
};
