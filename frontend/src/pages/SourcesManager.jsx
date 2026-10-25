import React, { useState, useEffect } from 'react';
import {
  Rss,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  Shield,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export default function SourcesManager() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [notice, setNotice] = useState(null);

  // Form state
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('tech_media');
  const [isOfficial, setIsOfficial] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchSources = async () => {
    setLoading(true);
    try {
      const data = await api.getSources();
      setSources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleToggleSource = async (src) => {
    try {
      const updated = await api.updateSource(src.id, { is_enabled: !src.is_enabled });
      setSources(sources.map((s) => (s.id === src.id ? updated : s)));
    } catch (err) {
      setNotice(`Failed to toggle: ${err.message}`);
    }
  };

  const handleDeleteSource = async (id) => {
    if (!window.confirm('Delete this news source? Associated articles and history will remain.')) return;
    try {
      await api.deleteSource(id);
      setSources(sources.filter((s) => s.id !== id));
      setNotice('Source removed.');
    } catch (err) {
      setNotice(`Failed to delete: ${err.message}`);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!name || !url) return;
    setSubmitting(true);
    try {
      const created = await api.createSource({
        name,
        url,
        category,
        is_official: isOfficial,
        feed_type: 'rss',
      });
      setSources([...sources, created]);
      setShowAddModal(false);
      setName('');
      setUrl('');
      setNotice(`Added source "${created.name}"!`);
    } catch (err) {
      setNotice(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
      setTimeout(() => setNotice(null), 4000);
    }
  };

  return (
    <div className="space-y-6 fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 font-editorial flex items-center gap-2">
            <Rss className="w-5 h-5 text-blue-600" />
            <span>Configured News Sources</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage RSS/Atom feeds for official AI labs, research publications, and technology newsrooms
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-all w-fit"
        >
          <Plus className="w-4 h-4" />
          <span>Add Custom Source</span>
        </button>
      </div>

      {notice && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg flex items-center justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
      )}

      {/* Table of Sources */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Source Name</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Reliability</th>
                <th className="py-3 px-4">Last Status</th>
                <th className="py-3 px-4">Last Fetched</th>
                <th className="py-3 px-4 text-center">Active</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sources.map((src) => (
                <tr key={src.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                      <span>{src.name}</span>
                      {src.is_official && (
                        <span className="bg-emerald-50 text-emerald-700 text-[9px] font-bold px-1.5 py-0.2 rounded border border-emerald-200" title="Primary Lab / Official PR">
                          OFFICIAL
                        </span>
                      )}
                    </div>
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-slate-400 hover:text-blue-600 font-mono truncate max-w-xs block"
                    >
                      {src.url}
                    </a>
                  </td>

                  <td className="py-3 px-4">
                    <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[11px] capitalize">
                      {src.category.replace('_', ' ')}
                    </span>
                  </td>

                  <td className="py-3 px-4 uppercase text-[10px] font-mono text-slate-500">
                    {src.feed_type}
                  </td>

                  <td className="py-3 px-4 font-mono font-medium text-slate-700">
                    {(src.reliability_score * 100).toFixed(0)}%
                  </td>

                  <td className="py-3 px-4">
                    {src.last_status === 'success' ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Success
                      </span>
                    ) : src.last_status === 'error' ? (
                      <span className="inline-flex items-center gap-1 text-rose-700 font-medium" title={src.last_error}>
                        <AlertCircle className="w-3.5 h-3.5 text-rose-500" /> Error
                      </span>
                    ) : (
                      <span className="text-slate-400">Pending</span>
                    )}
                  </td>

                  <td className="py-3 px-4 text-slate-500 text-[11px]">
                    {src.last_fetched_at ? new Date(src.last_fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}
                  </td>

                  <td className="py-3 px-4 text-center">
                    <input
                      type="checkbox"
                      checked={src.is_enabled}
                      onChange={() => handleToggleSource(src)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4 cursor-pointer"
                    />
                  </td>

                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDeleteSource(src.id)}
                      className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                      title="Delete Source"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Source Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h2 className="text-base font-bold text-slate-900 font-editorial">
              Add New News Source
            </h2>
            <form onSubmit={handleAddSubmit} className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-slate-700 block mb-1">Source Name</label>
                <input
                  type="text"
                  placeholder="e.g. DeepMind Research Blog"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">RSS / Atom URL</label>
                <input
                  type="url"
                  placeholder="https://example.com/feed.xml"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  Protected by SSRF security filtering. Localhost, loopback, and private IP targets are blocked.
                </p>
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="official_ai">Official AI Laboratory / Company</option>
                  <option value="research">Academic / Research Publication</option>
                  <option value="tech_media">Technology Newsroom</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is-official-check"
                  checked={isOfficial}
                  onChange={(e) => setIsOfficial(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                />
                <label htmlFor="is-official-check" className="text-slate-700 font-medium">
                  Official Primary Announcement Source
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold"
                >
                  {submitting ? 'Adding...' : 'Save Source'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
