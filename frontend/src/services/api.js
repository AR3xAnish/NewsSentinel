const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Ignore if body is not JSON
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  // Health & Stats
  getHealth: () => fetchJson('/health'),
  getOllamaHealth: () => fetchJson('/health/ollama'),
  getStats: () => fetchJson('/stats'),

  // News Stories
  getNews: (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.status_filter) query.set('status_filter', params.status_filter);
    if (params.page) query.set('page', params.page);
    if (params.limit) query.set('limit', params.limit);
    const qs = query.toString();
    return fetchJson(`/news${qs ? `?${qs}` : ''}`);
  },
  getStoryDetail: (storyId) => fetchJson(`/news/${storyId}`),
  verifyStory: (storyId) => fetchJson(`/news/${storyId}/verify`, { method: 'POST' }),
  summarizeStory: (storyId) => fetchJson(`/news/${storyId}/summarize`, { method: 'POST' }),

  // Sources
  getSources: () => fetchJson('/sources'),
  createSource: (sourceData) => fetchJson('/sources', {
    method: 'POST',
    body: JSON.stringify(sourceData),
  }),
  updateSource: (sourceId, sourceData) => fetchJson(`/sources/${sourceId}`, {
    method: 'PATCH',
    body: JSON.stringify(sourceData),
  }),
  deleteSource: (sourceId) => fetchJson(`/sources/${sourceId}`, {
    method: 'DELETE',
  }),

  // Collection & Runs
  triggerCollection: (options = {}) => fetchJson('/collect', {
    method: 'POST',
    body: JSON.stringify(options),
  }),
  getRuns: (limit = 20) => fetchJson(`/runs?limit=${limit}`),

  // Social Studio
  getSocialPosts: (params = {}) => {
    const query = new URLSearchParams();
    if (params.story_id) query.set('story_id', params.story_id);
    if (params.platform) query.set('platform', params.platform);
    const qs = query.toString();
    return fetchJson(`/social-posts${qs ? `?${qs}` : ''}`);
  },
  generateSocialPosts: (storyId, platforms) => fetchJson(`/news/${storyId}/social-posts/generate`, {
    method: 'POST',
    body: JSON.stringify({ platforms }),
  }),
  updateSocialPost: (postId, data) => fetchJson(`/social-posts/${postId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),
  regenerateSocialPost: (postId) => fetchJson(`/social-posts/${postId}/regenerate`, {
    method: 'POST',
  }),

  // Settings
  getSettings: () => fetchJson('/settings'),
  updateSetting: (key, value) => fetchJson(`/settings?key=${encodeURIComponent(key)}`, {
    method: 'PATCH',
    body: JSON.stringify({ value }),
  }),

  // Telegram
  testTelegram: (message) => fetchJson('/telegram/test', {
    method: 'POST',
    body: JSON.stringify({ message }),
  }),
  sendTelegramStory: (storyId, customNote) => fetchJson('/telegram/send', {
    method: 'POST',
    body: JSON.stringify({ story_id: storyId, custom_note: customNote }),
  }),
  previewDailyDigest: (maxStories = 5) => fetchJson(`/telegram/daily-digest/preview?max_stories=${maxStories}`),
  sendDailyDigest: (options = {}) => fetchJson('/telegram/daily-digest', {
    method: 'POST',
    body: JSON.stringify(options),
  }),
  getDeliveries: () => fetchJson('/deliveries'),
};
