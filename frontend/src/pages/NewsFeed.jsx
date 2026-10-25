import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Share2,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';

export default function NewsFeed({ onNavigateToStory, onNavigateToTab }) {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchNews = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getNews({
        search: search.trim() || undefined,
        status_filter: statusFilter !== 'ALL' ? statusFilter : undefined,
        page,
        limit: 10,
      });
      setStories(res.items || []);
      setTotalPages(res.total_pages || 1);
      setTotalCount(res.total || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchNews();
  };

  const filterOptions = [
    { id: 'ALL', label: 'All Stories' },
    { id: 'CORROBORATED', label: 'Corroborated' },
    { id: 'PARTIALLY_CORROBORATED', label: 'Partially Corroborated' },
    { id: 'CONFLICTING', label: 'Conflicting' },
    { id: 'INSUFFICIENT_EVIDENCE', label: 'Single-Source' },
    { id: 'UNVERIFIED', label: 'Unverified' },
  ];

  return (
    <div className="space-y-6 fade-in">
      {/* Header & Search */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 font-editorial">
              Intelligence News Feed
            </h1>
            <p className="text-xs text-slate-500">
              {totalCount} event stories clustered from verified RSS streams
            </p>
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-md w-full">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                id="search-news-input"
                type="text"
                placeholder="Search headlines, keywords, companies..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-slate-50/50"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-100">
          <span className="text-xs font-medium text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Filter:
          </span>
          {filterOptions.map((opt) => (
            <button
              key={opt.id}
              onClick={() => {
                setStatusFilter(opt.id);
                setPage(1);
              }}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                statusFilter === opt.id
                  ? 'bg-navy-900 text-white font-medium shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stories Listing */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400">
          <div className="inline-block animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mb-3" />
          <p className="text-sm">Loading intelligence stories...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm">
          Failed to load stories: {error}
        </div>
      ) : stories.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400">
          <p className="text-sm font-medium text-slate-600">No stories found matching your filter.</p>
          <p className="text-xs text-slate-400 mt-1">Try resetting the filter or running news collection.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {stories.map((story) => (
            <div
              key={story.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-300 transition-all flex flex-col gap-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <StatusBadge status={story.verification_status} confidence={story.confidence_score} />
                  {story.primary_source_name && (
                    <span className="text-xs font-medium text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                      {story.primary_source_name}
                    </span>
                  )}
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Layers className="w-3 h-3" />
                    {story.source_count} source{story.source_count > 1 ? 's' : ''} ({story.independent_source_count} publisher{story.independent_source_count > 1 ? 's' : ''})
                  </span>
                </div>

                {story.earliest_published_at && (
                  <div className="text-xs text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>
                      {new Date(story.earliest_published_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                )}
              </div>

              {/* Title */}
              <h2
                onClick={() => onNavigateToStory(story.id)}
                className="text-base sm:text-lg font-bold text-slate-900 hover:text-blue-600 cursor-pointer transition-colors font-editorial"
              >
                {story.headline}
              </h2>

              {/* Summary snippet */}
              {story.summary_factual && (
                <p className="text-xs sm:text-sm text-slate-600 line-clamp-2 leading-relaxed">
                  {story.summary_factual}
                </p>
              )}

              {/* Footer Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                {story.primary_source_url ? (
                  <a
                    href={story.primary_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-500 hover:text-slate-800 flex items-center gap-1 text-[11px] font-mono truncate max-w-xs"
                    title={story.primary_source_url}
                  >
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{new URL(story.primary_source_url).hostname}</span>
                  </a>
                ) : (
                  <div />
                )}

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      onNavigateToStory(story.id);
                      onNavigateToTab('social');
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-medium"
                  >
                    <Share2 className="w-3.5 h-3.5" />
                    <span>Social Studio</span>
                  </button>
                  <button
                    onClick={() => onNavigateToStory(story.id)}
                    className="flex items-center gap-1 px-3.5 py-1.5 text-xs font-semibold text-white bg-navy-900 hover:bg-navy-800 rounded-lg shadow-sm transition-colors"
                  >
                    <span>Inspect Claims</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Pagination */}
          <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
