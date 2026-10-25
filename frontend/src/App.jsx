import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import NewsFeed from './pages/NewsFeed';
import StoryDetail from './pages/StoryDetail';
import SocialStudio from './pages/SocialStudio';
import SourcesManager from './pages/SourcesManager';
import RunHistory from './pages/RunHistory';
import Settings from './pages/Settings';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedStoryId, setSelectedStoryId] = useState(null);
  const [stats, setStats] = useState(null);
  const [ollamaHealth, setOllamaHealth] = useState(null);
  const [recentStories, setRecentStories] = useState([]);
  const [isCollecting, setIsCollecting] = useState(false);

  const loadInitialData = async () => {
    try {
      const [statsData, ollamaData, newsData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getOllamaHealth().catch(() => null),
        api.getNews({ limit: 10 }).catch(() => ({ items: [] })),
      ]);
      setStats(statsData);
      setOllamaHealth(ollamaData);
      setRecentStories(newsData.items || []);
    } catch (err) {
      console.error('Initialization error:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleTriggerCollect = async () => {
    setIsCollecting(true);
    try {
      const res = await api.triggerCollection();
      await loadInitialData();
      return res;
    } finally {
      setIsCollecting(false);
    }
  };

  const handleNavigateToStory = (storyId) => {
    setSelectedStoryId(storyId);
    setActiveTab('story');
  };

  const handleBackToFeed = () => {
    setActiveTab('feed');
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col text-slate-800">
      {/* Top Navigation */}
      <Navigation
        activeTab={activeTab === 'story' ? 'feed' : activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
        }}
        ollamaHealth={ollamaHealth}
        onTriggerCollect={handleTriggerCollect}
        isCollecting={isCollecting}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard
            stats={stats}
            ollamaHealth={ollamaHealth}
            recentStories={recentStories}
            onNavigateToStory={handleNavigateToStory}
            onNavigateToTab={setActiveTab}
            onTriggerCollect={handleTriggerCollect}
            isCollecting={isCollecting}
            refreshDashboard={loadInitialData}
          />
        )}

        {activeTab === 'feed' && (
          <NewsFeed
            onNavigateToStory={handleNavigateToStory}
            onNavigateToTab={setActiveTab}
          />
        )}

        {activeTab === 'story' && (
          <StoryDetail
            storyId={selectedStoryId}
            onBack={handleBackToFeed}
            onNavigateToTab={setActiveTab}
          />
        )}

        {activeTab === 'social' && (
          <SocialStudio
            selectedStoryId={selectedStoryId}
            onNavigateToStory={handleNavigateToStory}
          />
        )}

        {activeTab === 'sources' && (
          <SourcesManager />
        )}

        {activeTab === 'runs' && (
          <RunHistory />
        )}

        {activeTab === 'settings' && (
          <Settings
            ollamaHealth={ollamaHealth}
            refreshOllamaHealth={async () => {
              const h = await api.getOllamaHealth();
              setOllamaHealth(h);
            }}
          />
        )}
      </main>

      {/* Editorial Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-700">YGF News Intelligence</span>
            <span>•</span>
            <span>Local AI News Evaluation System</span>
          </div>
          <div className="text-[11px] text-slate-400">
            Powered by Ollama Local LLMs • Zero Paid Inference APIs • Deterministic Evidence Adjudication
          </div>
        </div>
      </footer>
    </div>
  );
}
