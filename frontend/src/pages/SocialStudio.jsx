import React, { useState, useEffect } from 'react';
import {
  Share2,
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Save,
  Layers,
  Sparkles
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';

export default function SocialStudio({ selectedStoryId, onNavigateToStory }) {
  const [stories, setStories] = useState([]);
  const [activeStoryId, setActiveStoryId] = useState(selectedStoryId || null);
  const [currentStory, setCurrentStory] = useState(null);
  const [posts, setPosts] = useState([]);
  const [activePlatform, setActivePlatform] = useState('linkedin');
  const [loading, setLoading] = useState(false);
  const [draftContent, setDraftContent] = useState('');
  const [copied, setCopied] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  // Load available stories for dropdown
  useEffect(() => {
    api.getNews({ limit: 30 }).then((res) => {
      setStories(res.items || []);
      if (!activeStoryId && res.items?.length > 0) {
        setActiveStoryId(res.items[0].id);
      }
    }).catch(console.error);
  }, []);

  // When selected story ID prop changes
  useEffect(() => {
    if (selectedStoryId) {
      setActiveStoryId(selectedStoryId);
    }
  }, [selectedStoryId]);

  // Load details and posts for active story
  useEffect(() => {
    if (activeStoryId) {
      loadStoryData(activeStoryId);
    }
  }, [activeStoryId]);

  const loadStoryData = async (id) => {
    setLoading(true);
    setSaveStatus(null);
    try {
      const [storyData, postList] = await Promise.all([
        api.getStoryDetail(id),
        api.getSocialPosts({ story_id: id }),
      ]);
      setCurrentStory(storyData);
      setPosts(postList);

      // Set active draft content
      const matched = postList.find((p) => p.platform === activePlatform);
      if (matched) {
        setDraftContent(matched.content);
      } else {
        setDraftContent('');
      }
    } catch (err) {
      console.error('Failed to load story posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlatformChange = (plat) => {
    setActivePlatform(plat);
    const matched = posts.find((p) => p.platform === plat);
    setDraftContent(matched ? matched.content : '');
  };

  const handleGenerateAll = async () => {
    if (!activeStoryId) return;
    setLoading(true);
    setSaveStatus('Generating platform drafts with local LLM...');
    try {
      const generated = await api.generateSocialPosts(activeStoryId, ['linkedin', 'x', 'instagram']);
      setPosts(generated);
      const matched = generated.find((p) => p.platform === activePlatform);
      if (matched) setDraftContent(matched.content);
      setSaveStatus('Drafts generated successfully!');
    } catch (err) {
      setSaveStatus(`Generation failed: ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setSaveStatus(null), 4000);
    }
  };

  const handleSaveDraft = async () => {
    const currentPost = posts.find((p) => p.platform === activePlatform);
    if (!currentPost) return;

    try {
      const updated = await api.updateSocialPost(currentPost.id, {
        content: draftContent,
        status: 'DRAFT',
      });
      setPosts(posts.map((p) => (p.id === updated.id ? updated : p)));
      setSaveStatus('Draft saved!');
    } catch (err) {
      setSaveStatus(`Save failed: ${err.message}`);
    } finally {
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleCopyClipboard = () => {
    if (!draftContent) return;
    navigator.clipboard.writeText(draftContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currentPost = posts.find((p) => p.platform === activePlatform);
  const charLimit = activePlatform === 'x' ? 280 : 3000;
  const isOverLimit = activePlatform === 'x' && draftContent.length > 280;

  return (
    <div className="space-y-6 fade-in max-w-6xl mx-auto">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 font-editorial flex items-center gap-2">
            <Share2 className="w-5 h-5 text-blue-600" />
            <span>Social Studio</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Produce accurate, grounded social media drafts for LinkedIn, X (Twitter), and Instagram
          </p>
        </div>

        {/* Story Selector Dropdown */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <label htmlFor="story-select" className="text-xs font-medium text-slate-500 whitespace-nowrap">
            Active Story:
          </label>
          <select
            id="story-select"
            value={activeStoryId || ''}
            onChange={(e) => setActiveStoryId(Number(e.target.value))}
            className="text-xs border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-sm w-full truncate"
          >
            {stories.map((s) => (
              <option key={s.id} value={s.id}>
                [{s.verification_status}] {s.headline.slice(0, 50)}...
              </option>
            ))}
          </select>
        </div>
      </div>

      {saveStatus && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg flex items-center justify-between">
          <span>{saveStatus}</span>
          <button onClick={() => setSaveStatus(null)} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
      )}

      {/* Main Grid: Studio Editor (Left) & Grounded Source Evidence (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editor (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Platform Tabs */}
          <div className="bg-white p-2 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between gap-2">
            <div className="flex space-x-1">
              {[
                { id: 'linkedin', label: 'LinkedIn', icon: '💼' },
                { id: 'x', label: 'X (Twitter)', icon: '𝕏' },
                { id: 'instagram', label: 'Instagram', icon: '📸' },
              ].map((plat) => (
                <button
                  key={plat.id}
                  onClick={() => handlePlatformChange(plat.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activePlatform === plat.id
                      ? 'bg-navy-900 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span>{plat.icon}</span>
                  <span>{plat.label}</span>
                </button>
              ))}
            </div>

            <button
              onClick={handleGenerateAll}
              disabled={loading || !activeStoryId}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Regenerate Drafts</span>
            </button>
          </div>

          {/* Draft Content Card */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase tracking-wider text-slate-700">
                {activePlatform.toUpperCase()} DRAFT CONTENT
              </span>

              {/* Character Counter */}
              <div className="flex items-center gap-2">
                <span
                  className={`font-mono text-xs font-semibold px-2 py-0.5 rounded ${
                    isOverLimit
                      ? 'bg-rose-100 text-rose-700 border border-rose-300'
                      : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {draftContent.length} / {charLimit} chars
                </span>
                {isOverLimit && (
                  <span className="text-[10px] text-rose-600 font-medium">Exceeds 280 limit!</span>
                )}
              </div>
            </div>

            {/* Editable Textarea */}
            <textarea
              id="social-draft-textarea"
              rows={12}
              value={draftContent}
              onChange={(e) => setDraftContent(e.target.value)}
              placeholder="Draft text will appear here. You can edit and format directly..."
              className={`w-full p-4 text-xs sm:text-sm font-sans rounded-xl border focus:outline-none focus:ring-2 bg-slate-50/50 resize-y leading-relaxed ${
                isOverLimit
                  ? 'border-rose-300 focus:ring-rose-500'
                  : 'border-slate-300 focus:ring-blue-500'
              }`}
            />

            {/* Editorial Policy Warning */}
            <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg text-amber-900 text-xs">
              <strong>Human-in-the-Loop Requirement:</strong> Social posts are kept in draft state. Review accuracy, tone, and character count before publishing externally.
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <span className="text-[11px] text-slate-400">
                Status: <strong className="text-slate-600">{currentPost?.status || 'DRAFT'}</strong>
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleSaveDraft}
                  disabled={loading}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Draft</span>
                </button>
                <button
                  id="btn-copy-draft"
                  onClick={handleCopyClipboard}
                  className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-all"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied!' : 'Copy to Clipboard'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Grounded Evidence & Source Details */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <span>Grounded Evidence Context</span>
            </h2>

            {currentStory ? (
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 text-[11px] block">Story Headline</span>
                  <p className="font-semibold text-slate-900 mt-0.5">{currentStory.headline}</p>
                </div>

                <div>
                  <span className="text-slate-400 text-[11px] block">Verification Status</span>
                  <div className="mt-1">
                    <StatusBadge status={currentStory.verification_status} confidence={currentStory.confidence_score} size="sm" />
                  </div>
                </div>

                {currentStory.summary_factual && (
                  <div>
                    <span className="text-slate-400 text-[11px] block">Core Factual Summary</span>
                    <p className="text-slate-600 bg-slate-50 p-2.5 rounded border border-slate-200 mt-1 leading-relaxed">
                      {currentStory.summary_factual}
                    </p>
                  </div>
                )}

                {/* Primary Source URL */}
                <div>
                  <span className="text-slate-400 text-[11px] block">Attributed Source Links</span>
                  <div className="space-y-1.5 mt-1">
                    {currentStory.articles?.map((art) => (
                      <a
                        key={art.article_id}
                        href={art.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 rounded bg-slate-50 border border-slate-200 hover:border-blue-400 flex items-center justify-between gap-2 text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        <span className="truncate font-medium text-slate-800">{art.publisher}</span>
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => onNavigateToStory(currentStory.id)}
                  className="w-full text-center text-xs font-semibold text-blue-600 hover:underline pt-2 block"
                >
                  View Full Claim Evidence Breakdown →
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-400">Select a story to view grounded evidence.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
