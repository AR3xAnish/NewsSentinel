import React, { useState } from 'react';
import {
  LayoutDashboard,
  Newspaper,
  Share2,
  Rss,
  History,
  Settings as SettingsIcon,
  RefreshCw,
  Cpu,
  Send,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

export default function Navigation({
  activeTab,
  setActiveTab,
  ollamaHealth,
  onTriggerCollect,
  isCollecting
}) {
  const [collectionNotice, setCollectionNotice] = useState(null);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'feed', label: 'News Feed', icon: Newspaper },
    { id: 'social', label: 'Social Studio', icon: Share2 },
    { id: 'sources', label: 'Sources', icon: Rss },
    { id: 'runs', label: 'Run History', icon: History },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  const handleCollectClick = async () => {
    setCollectionNotice('Starting news collection...');
    try {
      const res = await onTriggerCollect();
      if (res && res.success) {
        setCollectionNotice(`Ingested ${res.articles_collected} articles (${res.duplicates_detected} duplicates skipped).`);
      } else {
        setCollectionNotice(res?.error || 'Collection finished with issues.');
      }
    } catch (err) {
      setCollectionNotice(`Error: ${err.message}`);
    }
    setTimeout(() => setCollectionNotice(null), 5000);
  };

  return (
    <header className="bg-navy-900 border-b border-navy-800 text-white sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-md">
              YGF
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-editorial text-lg tracking-wide font-bold">
                  YGF News Intelligence
                </span>
                <span className="text-[10px] bg-blue-900/80 border border-blue-700/60 text-blue-200 px-2 py-0.5 rounded uppercase font-semibold">
                  Local AI Agent
                </span>
              </div>
              <p className="text-xs text-slate-400">Grounded Fact Verification & Social Media Engine</p>
            </div>
          </div>

          {/* Right Status & Actions */}
          <div className="flex items-center gap-4">
            {/* Ollama Status Badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-850 border border-navy-700/60 text-xs">
              <Cpu className={`w-3.5 h-3.5 ${ollamaHealth?.connected ? 'text-emerald-400' : 'text-amber-400'}`} />
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 leading-tight">Local LLM</span>
                <span className="font-medium text-slate-200 leading-tight flex items-center gap-1">
                  {ollamaHealth?.configured_model || 'qwen3:4b'}
                  {ollamaHealth?.connected ? (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" title="Connected to Ollama" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" title="Ollama offline or model missing" />
                  )}
                </span>
              </div>
            </div>

            {/* Quick Collect Action */}
            <button
              id="btn-run-collection"
              onClick={handleCollectClick}
              disabled={isCollecting}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all ${
                isCollecting
                  ? 'bg-blue-800 text-blue-200 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 text-white hover:shadow-blue-500/20'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isCollecting ? 'animate-spin' : ''}`} />
              <span>{isCollecting ? 'Collecting...' : 'Run Collection'}</span>
            </button>
          </div>
        </div>

        {/* Global Notice Banner if present */}
        {collectionNotice && (
          <div className="bg-blue-950/90 border border-blue-700/60 text-blue-200 px-3 py-1.5 text-xs rounded mb-2 flex items-center justify-between">
            <span>{collectionNotice}</span>
            <button onClick={() => setCollectionNotice(null)} className="text-slate-400 hover:text-white ml-2 text-xs">✕</button>
          </div>
        )}

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 sm:space-x-4 border-t border-navy-800/80 pt-1 -mb-px overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`nav-tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-2 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-blue-500 text-blue-400 bg-navy-850/50 rounded-t'
                    : 'border-transparent text-slate-300 hover:text-white hover:border-slate-500'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
