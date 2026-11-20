import React, { useEffect, useState } from 'react';
import { Newspaper, ExternalLink, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { NewsArticle } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

export const MarketIntelligence: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [sentimentFilter, setSentimentFilter] = useState<string>('');

  const fetchNews = async () => {
    try {
      setLoading(true);
      const data = await api.getNews(0, 50, undefined, sentimentFilter || undefined);
      setArticles(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, [sentimentFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Market Intelligence & Disclosures Feed
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized filings ingested from BSE Corporate Disclosures and Economic Times Markets.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={sentimentFilter}
            onChange={(e) => setSentimentFilter(e.target.value)}
            className="bg-navy-850 text-slate-200 text-xs font-mono px-3 py-2 rounded-lg border border-navy-750 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Sentiments</option>
            <option value="BULLISH">Bullish Catalysts</option>
            <option value="BEARISH">Bearish Risks</option>
            <option value="NEUTRAL">Neutral Developments</option>
          </select>
          <button
            onClick={fetchNews}
            className="p-2 bg-navy-850 hover:bg-navy-800 text-cyan-400 border border-navy-750 rounded-lg transition-all"
            title="Refresh News"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Ingesting real-time Indian stock market disclosures..." />
      ) : articles.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {articles.map((item) => (
            <div
              key={item.id}
              className="glass-panel glass-panel-hover rounded-xl p-5 space-y-3 transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {item.source}
                    </span>
                    {item.sentiment && <StatusBadge status={item.sentiment} />}
                    {item.sentiment_score !== null && (
                      <span className="text-[10px] font-mono text-slate-400">
                        Score: {Number(item.sentiment_score).toFixed(2)}
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-semibold text-white leading-snug">
                    {item.title}
                  </h3>
                </div>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors whitespace-nowrap self-start"
                >
                  <span>Source Filing</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>

              {item.summary && (
                <p className="text-xs text-slate-400 leading-relaxed font-sans">
                  {item.summary}
                </p>
              )}

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 border-t border-navy-800/60 pt-2.5">
                <span>Article ID: #{item.id}</span>
                <span>
                  {new Date(item.created_at).toLocaleString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })} IST
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No News Disclosures Ingested"
          description="Awaiting evening batch trigger or n8n workflow webhook execution."
          icon={Newspaper}
        />
      )}
    </div>
  );
};
