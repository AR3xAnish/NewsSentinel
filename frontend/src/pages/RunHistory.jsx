import React, { useState, useEffect } from 'react';
import {
  History,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Layers,
  FileText
} from 'lucide-react';
import { api } from '../services/api';

export default function RunHistory() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedRunId, setExpandedRunId] = useState(null);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.getRuns(30);
      setRuns(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const calculateDuration = (start, finish) => {
    if (!start || !finish) return 'In progress...';
    const s = new Date(start);
    const f = new Date(finish);
    const diffSec = Math.round((f - s) / 1000);
    return `${diffSec}s`;
  };

  return (
    <div className="space-y-6 fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 font-editorial flex items-center gap-2">
            <History className="w-5 h-5 text-blue-600" />
            <span>Collection Run Audit History</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Complete audit trail of automated and manual news ingestion runs, duplicate counts, and diagnostic logs
          </p>
        </div>

        <button
          onClick={fetchRuns}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Audit Log</span>
        </button>
      </div>

      {/* Runs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Started At</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Sources</th>
                <th className="py-3 px-4">Articles Collected</th>
                <th className="py-3 px-4">Duplicates Filtered</th>
                <th className="py-3 px-4">Stories Created</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.map((r) => {
                const isExpanded = expandedRunId === r.id;
                return (
                  <React.Fragment key={r.id}>
                    <tr className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-700">
                        #{r.id}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                            r.run_type === 'scheduled'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {r.run_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {new Date(r.started_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-600">
                        {calculateDuration(r.started_at, r.finished_at)}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {r.sources_successful} / {r.sources_attempted}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        +{r.articles_collected}
                      </td>
                      <td className="py-3 px-4 text-slate-500 font-mono">
                        {r.duplicates_detected}
                      </td>
                      <td className="py-3 px-4 font-bold text-indigo-700">
                        {r.stories_created}
                      </td>
                      <td className="py-3 px-4">
                        {r.status === 'success' ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Success
                          </span>
                        ) : r.status === 'partial_failure' ? (
                          <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-500" /> Partial
                          </span>
                        ) : r.status === 'running' ? (
                          <span className="inline-flex items-center gap-1 text-blue-700 font-medium">
                            <RefreshCw className="w-3.5 h-3.5 text-blue-500 animate-spin" /> In Progress
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-rose-700 font-medium">
                            <AlertCircle className="w-3.5 h-3.5 text-rose-500" /> Failed
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {r.error_log ? (
                          <button
                            onClick={() => setExpandedRunId(isExpanded ? null : r.id)}
                            className="text-xs text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                          >
                            <span>Logs</span>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        ) : (
                          <span className="text-slate-300 text-[10px]">No errors</span>
                        )}
                      </td>
                    </tr>

                    {/* Expandable error log panel */}
                    {isExpanded && r.error_log && (
                      <tr className="bg-slate-900 text-slate-200">
                        <td colSpan={10} className="p-4 text-xs font-mono whitespace-pre-wrap leading-relaxed">
                          <div className="text-[10px] text-rose-400 font-bold uppercase mb-1">
                            Diagnostic Error Logs (Run #{r.id}):
                          </div>
                          {r.error_log}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {runs.length === 0 && (
          <div className="p-10 text-center text-slate-400 text-sm">
            No collection runs recorded yet. Click "Run Collection" in the navigation bar to start the first pass.
          </div>
        )}
      </div>
    </div>
  );
}
