import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Overview } from './pages/Overview';
import { MarketIntelligence } from './pages/MarketIntelligence';
import { AiAgents } from './pages/AiAgents';
import { TradingDecisions } from './pages/TradingDecisions';
import { RiskManagement } from './pages/RiskManagement';
import { PaperTrading } from './pages/PaperTrading';
import { AgentActivity } from './pages/AgentActivity';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/20 selection:text-cyan-300">
        <Navbar />
        <div className="flex-1 flex flex-col md:flex-row">
          <Sidebar />
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto w-full max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/intelligence" element={<MarketIntelligence />} />
              <Route path="/agents" element={<AiAgents />} />
              <Route path="/decisions" element={<TradingDecisions />} />
              <Route path="/risk" element={<RiskManagement />} />
              <Route path="/paper-trading" element={<PaperTrading />} />
              <Route path="/activity" element={<AgentActivity />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
