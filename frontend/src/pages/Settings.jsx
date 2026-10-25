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
  ExternalLink
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
    </div>
  );
}
