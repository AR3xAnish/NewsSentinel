import React, { useState } from 'react';
import {
  FileText,
  Layers,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Clock,
  ArrowRight,
  ExternalLink,
  Cpu,
  RefreshCw,
  Share2,
  Newspaper,
  Send,
  Calendar
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';

export default function Dashboard({
  stats,
  ollamaHealth,
  recentStories,
  onNavigateToStory,
  onNavigateToTab,
  onTriggerCollect,
  isCollecting,
  refreshDashboard
}) {
  const [sendingDailyDigest, setSendingDailyDigest] = useState(false);
  const [dailyDigestNotice, setDailyDigestNotice] = useState(null);

  const handleDispatchDailyDigest = async () => {
    setSendingDailyDigest(true);
    try {
      const res = await api.sendDailyDigest({ force_collect: true, max_stories: 5 });
      if (res.success) {
        setDailyDigestNotice(`Daily News Brief sent to Telegram! (${res.stories_count || 0} stories)`);
      } else {
        setDailyDigestNotice(`Dispatch error: ${res.error}`);
      }
    } catch (err) {
      setDailyDigestNotice(`Dispatch error: ${err.message}`);
    } finally {
      setSendingDailyDigest(false);
      setTimeout(() => setDailyDigestNotice(null), 5000);
    }
  };

  const chartData = [
    { name: 'Corroborated', value: stats?.corroborated_stories || 0, color: '#10b981' },
    { name: 'Partially Corroborated', value: stats?.partially_corroborated_stories || 0, color: '#f59e0b' },
    { name: 'Conflicting', value: stats?.conflicting_stories || 0, color: '#f43f5e' },
    { name: 'Single-Source / Insufficient', value: stats?.insufficient_evidence_stories || 0, color: '#a855f7' },
    { name: 'Unverified', value: stats?.unverified_stories || 0, color: '#94a3b8' },
  ].filter(d => d.value > 0);

  const formatTime = (ts) => {
    if (!ts) return 'Never';
    return new Date(ts).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Top Welcome & Subtitle */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-editorial">
            Editorial Intelligence Overview
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Real-time multi-source AI news monitoring, cross-verification, and automated social publishing.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleDispatchDailyDigest}
            disabled={sendingDailyDigest}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg shadow-sm transition-all"
            title="Dispatch today's curated news digest to Telegram"
          >
            <Send className="w-3.5 h-3.5 text-emerald-600" />
            <span>{sendingDailyDigest ? 'Dispatching...' : 'Send Daily News'}</span>
          </button>
          <button
            onClick={refreshDashboard}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => onNavigateToTab('feed')}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-navy-900 hover:bg-navy-800 rounded-lg shadow-sm transition-all"
          >
            <span>Browse Full Feed</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Daily Digest Notice Banner */}
      {dailyDigestNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs rounded-xl flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <Send className="w-4 h-4 text-emerald-600" />
            <span className="font-medium">{dailyDigestNotice}</span>
          </div>
          <button
            onClick={() => setDailyDigestNotice(null)}
            className="text-slate-400 hover:text-slate-600 font-bold px-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Ollama Local Engine Status Banner if offline or unconfigured */}
      {!ollamaHealth?.connected && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3">
          <Cpu className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">
            <span className="font-semibold">Local LLM Offline or Missing: </span>
            <span>{ollamaHealth?.message || 'Ollama HTTP server not reachable at http://localhost:11434.'}</span>
            <div className="mt-1 text-xs text-amber-800">
              News ingestion, deduplication, and deterministic rule-based verification continue to run independently.
              To enable local AI summaries and claim extraction, start Ollama and run <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">ollama pull {ollamaHealth?.configured_model || 'qwen3:4b'}</code>.
            </div>
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Articles */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Articles</span>
            <FileText className="w-4 h-4 text-blue-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{stats?.total_articles || 0}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Ingested via RSS</div>
          </div>
        </div>

        {/* Unique Stories */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Clustered Stories</span>
            <Layers className="w-4 h-4 text-indigo-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{stats?.total_stories || 0}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Event groups</div>
          </div>
        </div>

        {/* Corroborated */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Corroborated</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-700">{stats?.corroborated_stories || 0}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Multi-source verified</div>
          </div>
        </div>

        {/* Conflicting */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-rose-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Conflicting</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-rose-700">{stats?.conflicting_stories || 0}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Discrepancies found</div>
          </div>
        </div>

        {/* Single-Source / Insufficient */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-purple-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Single-Source</span>
            <HelpCircle className="w-4 h-4 text-purple-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-700">{stats?.insufficient_evidence_stories || 0}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Awaiting cross-sources</div>
          </div>
        </div>

        {/* Last Collection Run */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Last Sync</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-900 truncate">
              {formatTime(stats?.last_collection_time)}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5 capitalize">
              Status: <span className="font-medium text-slate-700">{stats?.last_run_status || 'Never'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Middle Section: Chart & Intelligence Methodology */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Verification Breakdown Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center justify-between">
            <span>Verification Status Distribution</span>
            <span className="text-xs font-normal text-slate-500">{stats?.total_stories || 0} total stories</span>
          </h2>
          {chartData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-sm">
              <p>No stories collected yet.</p>
              <button
                onClick={onTriggerCollect}
                disabled={isCollecting}
                className="mt-3 text-xs text-blue-600 hover:underline"
              >
                Run initial collection now
              </button>
            </div>
          )}
        </div>

        {/* Verification Principles & Heuristic Notes */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-2">
              Cross-Validation Integrity Principles
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              This system does not treat LLM outputs as proof of truth. Claims are verified through a deterministic rule engine evaluating independent source reporting:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 text-xs">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-semibold text-slate-800 block mb-1">1. Independence Over Count</span>
                <p className="text-slate-600">Multiple republished copies of the same press release count as a single origin source.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-semibold text-slate-800 block mb-1">2. Discrepancy Flagging</span>
                <p className="text-slate-600">Material conflicts in numerical figures, launch dates, or benchmark claims are marked as CONFLICTING.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-semibold text-slate-800 block mb-1">3. Transparent Heuristics</span>
                <p className="text-slate-600">Confidence scores are explicitly calculated from source count, independence, and lack of contradictions.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-semibold text-slate-800 block mb-1">4. Human Editorial Oversight</span>
                <p className="text-slate-600">Social drafts are kept in DRAFT state requiring human review and approval before external dispatch.</p>
              </div>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Configured Local Model: <strong className="text-slate-700">{ollamaHealth?.configured_model}</strong></span>
            <button
              onClick={() => onNavigateToTab('settings')}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Configure Settings →
            </button>
          </div>
        </div>
      </div>

      {/* Recent Intelligence Stories */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 font-editorial">
              Recent Intelligence Stories
            </h2>
            <p className="text-xs text-slate-500">Latest clustered news with verification assessments</p>
          </div>
          <button
            onClick={() => onNavigateToTab('feed')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span>View All Stories</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentStories && recentStories.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {recentStories.slice(0, 6).map((story) => (
              <div
                key={story.id}
                className="p-5 hover:bg-slate-50/80 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <StatusBadge status={story.verification_status} confidence={story.confidence_score} size="sm" />
                    {story.primary_source_name && (
                      <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                        {story.primary_source_name}
                      </span>
                    )}
                    <span className="text-[11px] text-slate-400">
                      {story.source_count} article{story.source_count > 1 ? 's' : ''} ({story.independent_source_count} publisher{story.independent_source_count > 1 ? 's' : ''})
                    </span>
                  </div>

                  <h3
                    onClick={() => onNavigateToStory(story.id)}
                    className="text-sm font-semibold text-slate-900 hover:text-blue-600 cursor-pointer transition-colors"
                  >
                    {story.headline}
                  </h3>

                  {story.summary_factual && (
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                      {story.summary_factual}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => onNavigateToStory(story.id)}
                    className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg transition-colors"
                  >
                    Inspect Evidence
                  </button>
                  <button
                    onClick={() => {
                      onNavigateToStory(story.id);
                      onNavigateToTab('social');
                    }}
                    className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Generate Social Drafts"
                  >
                    <Share2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-10 text-center text-slate-400">
            <Newspaper className="w-8 h-8 mx-auto text-slate-300 mb-2" />
            <p className="text-sm">No stories in the database yet.</p>
            <p className="text-xs text-slate-400 mt-1">Click "Run Collection" to fetch and verify live AI news feeds.</p>
          </div>
        )}
      </div>
    </div>
  );
}
