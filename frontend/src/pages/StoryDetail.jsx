import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  RefreshCw,
  Share2,
  Send,
  ExternalLink,
  ShieldCheck,
  Calendar,
  Layers,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  FileText,
  Clock,
  Sparkles
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';

export default function StoryDetail({
  storyId,
  onBack,
  onNavigateToTab
}) {
  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStoryDetail(storyId);
      setStory(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (storyId) {
      fetchDetail();
    }
  }, [storyId]);

  const handleReVerify = async () => {
    setIsProcessing(true);
    setActionNotice('Running claim extraction and cross-validation...');
    try {
      await api.verifyStory(storyId);
      await fetchDetail();
      setActionNotice('Verification complete!');
    } catch (err) {
      setActionNotice(`Verification failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setActionNotice(null), 4000);
    }
  };

  const handleReSummarize = async () => {
    setIsProcessing(true);
    setActionNotice('Generating grounded summary with local LLM...');
    try {
      await api.summarizeStory(storyId);
      await fetchDetail();
      setActionNotice('Summary regenerated!');
    } catch (err) {
      setActionNotice(`Summarization failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setActionNotice(null), 4000);
    }
  };

  const handleSendTelegram = async () => {
    setIsProcessing(true);
    setActionNotice('Dispatching Telegram notification...');
    try {
      const res = await api.sendTelegramStory(storyId);
      if (res.success) {
        setActionNotice('Sent to Telegram chat successfully!');
      } else {
        setActionNotice(`Telegram dispatch failed: ${res.error}`);
      }
    } catch (err) {
      setActionNotice(`Error: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setActionNotice(null), 5000);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mb-3" />
        <p className="text-sm">Loading story intelligence details...</p>
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="p-6 bg-white rounded-xl border border-slate-200">
        <button onClick={onBack} className="text-xs text-blue-600 flex items-center gap-1 mb-4">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Feed
        </button>
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm">
          {error || 'Story not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in max-w-5xl mx-auto">
      {/* Top Navigation & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white px-3 py-1.5 rounded-lg border border-slate-300 shadow-sm w-fit transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Feed</span>
        </button>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleReVerify}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            <span>Re-Verify</span>
          </button>
          <button
            onClick={handleReSummarize}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>Re-Summarize</span>
          </button>
          <button
            onClick={handleSendTelegram}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors"
          >
            <Send className="w-3.5 h-3.5 text-sky-600" />
            <span>Send Telegram</span>
          </button>
          <button
            onClick={() => onNavigateToTab('social')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold bg-navy-900 hover:bg-navy-800 text-white rounded-lg shadow-sm transition-colors"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Open Social Studio</span>
          </button>
        </div>
      </div>

      {/* Action Notification Alert */}
      {actionNotice && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs px-4 py-2.5 rounded-lg flex items-center justify-between shadow-sm">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-slate-400 hover:text-slate-600 ml-2">✕</button>
        </div>
      )}

      {/* Main Story Header Card */}
      <div className="bg-white p-6 sm:p-8 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <StatusBadge status={story.verification_status} confidence={story.confidence_score} />
          <span className="text-xs text-slate-500 flex items-center gap-1 bg-slate-100 px-2.5 py-0.5 rounded">
            <Layers className="w-3.5 h-3.5" />
            {story.source_count} Article{story.source_count > 1 ? 's' : ''} ({story.independent_source_count} Independent Publisher{story.independent_source_count > 1 ? 's' : ''})
          </span>
          {story.ai_processed_at && (
            <span className="text-[11px] text-slate-400 flex items-center gap-1 ml-auto">
              <Clock className="w-3 h-3" />
              Verified {new Date(story.ai_processed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 font-editorial leading-tight">
          {story.headline}
        </h1>

        {/* Verification Explanation Box */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
          <div className="font-semibold text-slate-900 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <span>Verification Assessment & Heuristic Confidence</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            {story.verification_explanation || 'Evaluation in progress.'}
          </p>
        </div>
      </div>

      {/* Grounded Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* What Happened */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 font-sans">
            What Happened
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed">
            {story.what_happened || story.summary_factual || 'Summary awaiting generation.'}
          </p>
        </div>

        {/* Why It Matters */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 font-sans">
            Why It Matters
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed">
            {story.why_it_matters || 'Strategic analysis in progress.'}
          </p>
        </div>

        {/* Key Facts & Dates */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 font-sans">
            Key Facts & Stated Metrics
          </h2>
          {story.key_facts_dates && story.key_facts_dates.length > 0 ? (
            <ul className="space-y-2 text-xs">
              {story.key_facts_dates.map((item, idx) => (
                <li key={idx} className="p-2.5 rounded bg-slate-50 border border-slate-100 flex items-start justify-between gap-3">
                  <span className="text-slate-800 font-medium">{item.fact}</span>
                  {item.source && (
                    <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono flex-shrink-0">
                      {item.source}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic">No specific metric breakdown recorded.</p>
          )}
        </div>

        {/* What Remains Uncertain */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <h2 className="text-sm font-bold uppercase tracking-wider text-amber-700 font-sans flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-amber-600" />
            <span>What Remains Uncertain / Single-Source Limits</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-amber-50/50 p-3 rounded-lg border border-amber-100">
            {story.what_remains_uncertain || 'No known evidentiary contradictions detected.'}
          </p>
        </div>
      </div>

      {/* Claims & Evidence Breakdown Section */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 font-editorial">
            Extracted Factual Claims & Cross-Source Evidence
          </h2>
          <p className="text-xs text-slate-500">
            Individual claims cross-checked against independent source reports to identify corroboration or contradictions
          </p>
        </div>

        {story.claims && story.claims.length > 0 ? (
          <div className="space-y-4">
            {story.claims.map((claim, idx) => (
              <div key={claim.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-500 font-mono">Claim #{idx + 1}</span>
                    <StatusBadge status={claim.status} size="sm" />
                    <span className="text-[10px] uppercase font-semibold text-slate-400 bg-white border px-1.5 py-0.5 rounded">
                      {claim.claim_type}
                    </span>
                  </div>
                  {claim.source_publisher && (
                    <span className="text-xs text-slate-500">
                      Origin: <strong className="text-slate-700">{claim.source_publisher}</strong>
                    </span>
                  )}
                </div>

                <p className="text-sm font-semibold text-slate-900 bg-white p-3 rounded-lg border border-slate-200">
                  "{claim.claim_text}"
                </p>

                {claim.verification_notes && (
                  <p className="text-xs text-slate-600 italic">
                    Note: {claim.verification_notes}
                  </p>
                )}

                {/* Evidence Items for this Claim */}
                {claim.evidence_items && claim.evidence_items.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 space-y-2">
                    <span className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
                      Cross-Source Evidence Items ({claim.evidence_items.length})
                    </span>
                    <div className="grid grid-cols-1 gap-2">
                      {claim.evidence_items.map((ev) => {
                        const verdictColor = {
                          SUPPORTS: 'bg-emerald-50 text-emerald-800 border-emerald-200',
                          CONTRADICTS: 'bg-rose-50 text-rose-800 border-rose-200',
                          INSUFFICIENT: 'bg-slate-100 text-slate-700 border-slate-200',
                          NEUTRAL: 'bg-blue-50 text-blue-800 border-blue-200',
                        }[ev.verdict] || 'bg-slate-100 text-slate-700';

                        return (
                          <div key={ev.id} className="p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-800">
                                {ev.publisher_name || 'Contributing Source'}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${verdictColor}`}>
                                {ev.verdict}
                              </span>
                            </div>
                            <p className="text-slate-600 font-mono text-[11px] bg-slate-50 p-2 rounded">
                              "{ev.snippet}"
                            </p>
                            {ev.material_discrepancy && (
                              <div className="text-rose-700 font-medium text-[11px] flex items-center gap-1 pt-1">
                                <AlertTriangle className="w-3 h-3 text-rose-500 flex-shrink-0" />
                                <span>Discrepancy: {ev.material_discrepancy}</span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-slate-400 bg-slate-50 rounded-xl">
            <p className="text-xs">No claims extracted yet for this story.</p>
            <button
              onClick={handleReVerify}
              disabled={isProcessing}
              className="mt-2 text-xs font-semibold text-blue-600 hover:underline"
            >
              Trigger Claim Verification Now
            </button>
          </div>
        )}
      </div>

      {/* Clustered Source Articles Section */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 font-editorial">
            Clustered Source Articles & Traceable Links
          </h2>
          <p className="text-xs text-slate-500">
            Original publications reporting on this event, preserved with full attribution
          </p>
        </div>

        <div className="divide-y divide-slate-100">
          {story.articles.map((art) => (
            <div key={art.article_id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-800">{art.publisher}</span>
                  {art.is_primary && (
                    <span className="bg-blue-100 text-blue-800 font-semibold text-[10px] px-1.5 py-0.5 rounded">
                      PRIMARY
                    </span>
                  )}
                  {art.is_official && (
                    <span className="bg-emerald-100 text-emerald-800 font-semibold text-[10px] px-1.5 py-0.5 rounded">
                      OFFICIAL ANNOUNCEMENT
                    </span>
                  )}
                </div>
                <div className="text-slate-600 font-medium">{art.title}</div>
                {art.published_at && (
                  <div className="text-slate-400 text-[11px] flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>Published: {new Date(art.published_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>

              <a
                href={art.canonical_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors w-fit flex-shrink-0"
              >
                <span>Read Original</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
