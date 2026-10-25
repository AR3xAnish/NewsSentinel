import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  Send,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sliders,
  ExternalLink,
  Calendar,
  Newspaper,
  Bell,
  Eye,
  Check
} from 'lucide-react';
import { api } from '../services/api';

export default function Settings({ ollamaHealth, refreshOllamaHealth }) {
  const [settingsData, setSettingsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState(null);

  // Form states
  const [modelName, setModelName] = useState('qwen3:4b');
  const [schedulerInterval, setSchedulerInterval] = useState('60');
  const [testMessage, setTestMessage] = useState('Hello from YGF News Intelligence Agent!');
  const [sendingTest, setSendingTest] = useState(false);

  // Daily News Digest states
  const [dailyDigestEnabled, setDailyDigestEnabled] = useState(true);
  const [dailyDigestTime, setDailyDigestTime] = useState('09:00');
  const [sendingDailyDigest, setSendingDailyDigest] = useState(false);
  const [dailyDigestPreview, setDailyDigestPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const data = await api.getSettings();
      setSettingsData(data);
      if (data?.ollama?.configured_model) {
        setModelName(data.ollama.configured_model);
      }
      if (data?.scheduler?.interval_minutes) {
        setSchedulerInterval(String(data.scheduler.interval_minutes));
      }
      if (data?.daily_digest) {
        setDailyDigestEnabled(Boolean(data.daily_digest.enabled));
        if (data.daily_digest.time) {
          setDailyDigestTime(data.daily_digest.time);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveModel = async () => {
    try {
      await api.updateSetting('OLLAMA_MODEL', modelName.trim());
      await refreshOllamaHealth();
      setNotice(`Model preference updated to ${modelName}`);
    } catch (err) {
      setNotice(`Failed to update model: ${err.message}`);
    } finally {
      setTimeout(() => setNotice(null), 4000);
    }
  };

  const handleSaveInterval = async () => {
    try {
      await api.updateSetting('SCHEDULER_INTERVAL_MINUTES', schedulerInterval);
      setNotice(`Scheduler interval updated to ${schedulerInterval} minutes`);
    } catch (err) {
      setNotice(`Failed to update interval: ${err.message}`);
    } finally {
      setTimeout(() => setNotice(null), 4000);
    }
  };

  const handleSendTelegramTest = async () => {
    setSendingTest(true);
    try {
      const res = await api.testTelegram(testMessage);
      if (res.success) {
        setNotice('Test message delivered to Telegram!');
      } else {
        setNotice(`Telegram error: ${res.error}`);
      }
    } catch (err) {
      setNotice(`Error: ${err.message}`);
    } finally {
      setSendingTest(false);
      setTimeout(() => setNotice(null), 5000);
    }
  };

  const handleToggleDailyDigest = async (newVal) => {
    setDailyDigestEnabled(newVal);
    try {
      await api.updateSetting('DAILY_DIGEST_ENABLED', newVal ? 'true' : 'false');
      setNotice(`Daily automated news dispatch ${newVal ? 'enabled' : 'disabled'}`);
      fetchSettings();
    } catch (err) {
      setNotice(`Failed to update daily dispatch toggle: ${err.message}`);
    } finally {
      setTimeout(() => setNotice(null), 4000);
    }
  };

  const handleSaveDailyTime = async () => {
    try {
      await api.updateSetting('DAILY_DIGEST_TIME', dailyDigestTime.trim());
      setNotice(`Daily dispatch time updated to ${dailyDigestTime}`);
      fetchSettings();
    } catch (err) {
      setNotice(`Failed to update dispatch time: ${err.message}`);
    } finally {
      setTimeout(() => setNotice(null), 4000);
    }
  };

  const handleSendDailyDigestNow = async () => {
    setSendingDailyDigest(true);
    try {
      const res = await api.sendDailyDigest({ force_collect: true, max_stories: 5 });
      if (res.success) {
        setNotice(`Daily News Digest dispatched to Telegram! (${res.stories_count || 0} stories included)`);
      } else {
        setNotice(`Dispatch error: ${res.error}`);
      }
    } catch (err) {
      setNotice(`Error sending daily digest: ${err.message}`);
    } finally {
      setSendingDailyDigest(false);
      setTimeout(() => setNotice(null), 6000);
    }
  };

  const handleLoadPreview = async () => {
    setLoadingPreview(true);
    try {
      const res = await api.previewDailyDigest(5);
      setDailyDigestPreview(res.message);
    } catch (err) {
      setNotice(`Preview error: ${err.message}`);
    } finally {
      setLoadingPreview(false);
    }
  };

  return (
    <div className="space-y-6 fade-in max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 font-editorial flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-blue-600" />
          <span>System & Engine Settings</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure local Ollama inference, background scheduling, and optional Telegram delivery
        </p>
      </div>

      {notice && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg flex items-center justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
      )}

      {/* Ollama Local LLM Configuration Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-600" />
            <span>Local Ollama LLM Configuration</span>
          </h2>
          <button
            onClick={refreshOllamaHealth}
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Test Connection</span>
          </button>
        </div>

        {/* Health status banner */}
        <div
          className={`p-3.5 rounded-lg border text-xs flex items-start gap-2.5 ${
            ollamaHealth?.connected
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-amber-50 border-amber-200 text-amber-900'
          }`}
        >
          {ollamaHealth?.connected ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1 space-y-1">
            <span className="font-semibold block">
              {ollamaHealth?.connected ? 'Ollama Server Connected' : 'Ollama Offline / Unreachable'}
            </span>
            <p className="text-[11px] leading-relaxed">{ollamaHealth?.message}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="font-medium text-slate-700 block mb-1">Configured Model Name</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g. qwen3:4b or qwen2.5:3b"
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-slate-50 font-mono"
              />
              <button
                onClick={handleSaveModel}
                className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold"
              >
                Save
              </button>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">
              Supports open-weight models (qwen3:4b, qwen2.5:3b, llama3.2). Never uses paid APIs.
            </p>
          </div>

          <div>
            <label className="font-medium text-slate-700 block mb-1">Installed Local Models</label>
            <div className="p-2 border border-slate-200 rounded-lg bg-slate-50 font-mono text-[11px] min-h-[38px] flex items-center">
              {ollamaHealth?.available_models && ollamaHealth.available_models.length > 0 ? (
                <span>{ollamaHealth.available_models.join(', ')}</span>
              ) : (
                <span className="text-slate-400 italic">No models currently installed in Ollama</span>
              )}
            </div>
          </div>
        </div>

        {/* Windows Command Instructions */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1.5">
          <span className="font-semibold text-slate-900">Windows Ollama Quick Start:</span>
          <p className="text-[11px] text-slate-600">
            1. Ensure Ollama is installed on Windows from <a href="https://ollama.com" target="_blank" rel="noreferrer" className="text-blue-600 underline">ollama.com</a>.
          </p>
          <p className="text-[11px] text-slate-600">
            2. In PowerShell or Command Prompt, run:
          </p>
          <pre className="p-2 bg-slate-900 text-emerald-400 rounded text-[11px] font-mono">
            ollama pull {modelName || 'qwen3:4b'}
          </pre>
        </div>
      </div>

      {/* Scheduling Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-600" />
          <span>Automation & Scheduler Settings (APScheduler)</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="font-medium text-slate-700 block mb-1">Automated Run Interval (Minutes)</label>
            <div className="flex gap-2">
              <input
                type="number"
                min="5"
                max="1440"
                value={schedulerInterval}
                onChange={(e) => setSchedulerInterval(e.target.value)}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-slate-50 font-mono"
              />
              <button
                onClick={handleSaveInterval}
                className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold"
              >
                Update
              </button>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">
              Protected by single-instance mutex locks to prevent overlapping collection runs.
            </p>
          </div>

          <div>
            <label className="font-medium text-slate-700 block mb-1">Lookback & Limit Policy</label>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 text-xs space-y-1">
              <div>Default Lookback: <strong>48 Hours</strong></div>
              <div>Max Articles / Feed: <strong>10 articles per run</strong></div>
            </div>
          </div>
        </div>
      </div>

      {/* Telegram Notification Delivery Setup */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
            <Send className="w-4 h-4 text-sky-600" />
            <span>Telegram Bot Delivery (Optional)</span>
          </h2>
          <span
            className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
              settingsData?.telegram?.configured
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            {settingsData?.telegram?.configured ? 'Configured' : 'Not Configured (Disabled)'}
          </span>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          The system safely operates without Telegram credentials. When configured, selected verified news summaries can be pushed directly to your team channel or personal chat.
        </p>

        {/* Setup Instructions */}
        <div className="p-3.5 rounded-lg bg-sky-50/60 border border-sky-200 text-sky-950 text-xs space-y-1.5">
          <span className="font-semibold">How to setup Telegram:</span>
          <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-700">
            <li>Search for <code className="bg-white px-1 py-0.5 rounded font-mono">@BotFather</code> on Telegram and create a new bot to receive your API Token.</li>
            <li>Start a chat with your new bot or add it to a Telegram channel.</li>
            <li>Obtain your numeric Chat ID (e.g. from <code className="bg-white px-1 py-0.5 rounded font-mono">@userinfobot</code>).</li>
            <li>Add <code className="bg-white px-1 py-0.5 rounded font-mono">TELEGRAM_BOT_TOKEN</code> and <code className="bg-white px-1 py-0.5 rounded font-mono">TELEGRAM_CHAT_ID</code> into <code className="bg-white px-1 py-0.5 rounded font-mono">backend/.env</code>.</li>
          </ol>
        </div>

        {/* Test Ping */}
        <div className="pt-2 border-t border-slate-100 space-y-2 text-xs">
          <label className="font-medium text-slate-700 block">Dispatch Test Ping</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              placeholder="Test notification message..."
              className="flex-1 p-2 border border-slate-300 rounded-lg text-xs"
            />
            <button
              onClick={handleSendTelegramTest}
              disabled={sendingTest || !settingsData?.telegram?.configured}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-lg shadow-sm"
            >
              {sendingTest ? 'Sending...' : 'Send Test Notification'}
            </button>
          </div>
          {!settingsData?.telegram?.configured && (
            <p className="text-[10px] text-slate-400">
              Set credentials in backend/.env to enable test sending.
            </p>
          )}
        </div>
      </div>

      {/* Daily News Intelligence Digest (Telegram) */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <span>Daily AI News Intelligence Digest</span>
                <span className="text-[10px] font-normal px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  Telegram Delivery
                </span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Automatically scans RSS feeds, verifies top claims, and dispatches a curated news briefing once a day
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`text-xs px-3 py-1 rounded-full font-semibold border ${
                dailyDigestEnabled && settingsData?.telegram?.configured
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
            >
              {dailyDigestEnabled && settingsData?.telegram?.configured ? 'Active (Scheduled)' : 'Inactive / Paused'}
            </span>
          </div>
        </div>

        {/* Schedule & Timing Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-100 text-xs">
          <div className="space-y-3">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Automated Daily Dispatch Toggle
              </label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleToggleDailyDigest(!dailyDigestEnabled)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    dailyDigestEnabled ? 'bg-emerald-600' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      dailyDigestEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span className="text-slate-600 font-medium">
                  {dailyDigestEnabled ? 'Daily automated sending is ON' : 'Daily automated sending is PAUSED'}
                </span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Daily Delivery Time (24-Hour Format HH:MM)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={dailyDigestTime}
                  onChange={(e) => setDailyDigestTime(e.target.value)}
                  placeholder="09:00"
                  className="w-32 p-2 border border-slate-300 rounded-lg text-xs font-mono bg-slate-50 text-center font-bold"
                />
                <button
                  onClick={handleSaveDailyTime}
                  className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold"
                >
                  Save Schedule
                </button>
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                E.g. <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">09:00</code> for morning executive brief, or <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">18:30</code> for evening roundup.
              </p>
            </div>
          </div>

          <div className="space-y-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
            <div className="flex items-center gap-1.5 text-slate-700 font-semibold">
              <Clock className="w-3.5 h-3.5 text-indigo-600" />
              <span>Next Scheduled Daily Run:</span>
            </div>
            <div className="font-mono text-xs text-slate-800 font-bold bg-white p-2.5 rounded border border-slate-200">
              {settingsData?.daily_digest?.next_run
                ? new Date(settingsData.daily_digest.next_run).toLocaleString(undefined, {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZoneName: 'short'
                  })
                : dailyDigestEnabled
                ? `Every day at ${dailyDigestTime}`
                : 'Paused'}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              When triggered, the agent pulls active RSS feeds, cross-validates claims, builds an executive briefing, and posts it to Telegram chat <code className="font-mono text-slate-700">{settingsData?.telegram?.chat_id || 'ID'}</code>.
            </p>
          </div>
        </div>

        {/* Action Buttons: Send Now & Preview */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={handleSendDailyDigestNow}
              disabled={sendingDailyDigest || !settingsData?.telegram?.configured}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-lg shadow-sm transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{sendingDailyDigest ? 'Collecting & Dispatching...' : "Send Today's News Digest Now"}</span>
            </button>

            <button
              onClick={handleLoadPreview}
              disabled={loadingPreview}
              className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors"
            >
              <Eye className="w-3.5 h-3.5" />
              <span>{loadingPreview ? 'Loading...' : 'Preview Daily Digest'}</span>
            </button>
          </div>

          {!settingsData?.telegram?.configured && (
            <span className="text-[11px] text-amber-600 font-medium">
              ⚠️ Configure Telegram credentials above to enable daily dispatch.
            </span>
          )}
        </div>

        {/* Digest Preview Box */}
        {dailyDigestPreview && (
          <div className="p-4 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono space-y-2 border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 pb-2 border-b border-slate-800">
              <span className="font-bold text-slate-300">Telegram Daily Digest Preview</span>
              <button
                onClick={() => setDailyDigestPreview(null)}
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                ✕ Close Preview
              </button>
            </div>
            <div
              className="whitespace-pre-wrap leading-relaxed text-[11px] text-slate-200"
              dangerouslySetInnerHTML={{ __html: dailyDigestPreview }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
