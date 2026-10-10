/**
 * api.js — API Client untuk AniWatch Portal
 *
 * Fitur:
 * - Auto-detect base URL
 * - Token via Authorization header (mobile-friendly)
 * - Credentials include (cookie)
 * - Retry pada network error
 * - Error handling (jangan auto-clear token untuk HTTP_401 generic)
 */
const API = (() => {
  // ═══════════════════════════════════════════════════════════
  //  CONFIG
  // ═══════════════════════════════════════════════════════════
  const CONFIG = {
    baseUrl: localStorage.getItem("aniwatch_base_url")
             || window.location.origin,
    timeout: 30000,
    retries: 2,              // retry 2× pada network error
    retryDelay: 1000,        // jeda 1 detik antar retry
    debug: true,             // log detail
  };

  // ═══════════════════════════════════════════════════════════
  //  LOG HELPER
  // ═══════════════════════════════════════════════════════════
  function log(msg, ...args) {
    if (CONFIG.debug) {
      console.log("[API]", msg, ...args);
    }
  }

  function logError(msg, ...args) {
    console.error("[API]", msg, ...args);
  }

  function warn(msg, ...args) {
    console.warn("[API]", msg, ...args);
  }

  // ═══════════════════════════════════════════════════════════
  //  REQUEST HELPER
  // ═══════════════════════════════════════════════════════════
search: async (q, apiKey) => {
  const key = apiKey || localStorage.getItem("aniwatch_api_key");
  const data = await request(
    `/share/query?q=${encodeURIComponent(q)}`,
    {
      headers: key ? { "X-API-Key": key } : {},
    }
  );

  // Handle SEARCH_EMPTY → redirect ke empty page
  if (
    !data.success &&
    data.error &&
    data.error.code === "SEARCH_EMPTY"
  ) {
    const params = new URLSearchParams({
      q: q,
      endpoint: "/share/query",
      agent: JSON.stringify(data.error.details?.agent || {}),
    });
    window.location.href = `/error/empty.html?${params}`;
    return data;
  }

  return data;
}
return data;
  // ═══════════════════════════════════════════════════════════
  //  PUBLIC API
  // ═══════════════════════════════════════════════════════════
  return {
    // ─── Config ───
    baseUrl: () => CONFIG.baseUrl,
    setBaseUrl: (url) => {
      CONFIG.baseUrl = url;
      localStorage.setItem("aniwatch_base_url", url);
    },
    setDebug: (on) => {
      CONFIG.debug = !!on;
      return CONFIG.debug;
    },

    // ─── Health ───
    health: () => request("/health"),
    stats: () => request("/stats"),

    // ─── Auth ───
    register: (username, password, email) =>
      request("/register", {
        method: "POST",
        body: JSON.stringify({ username, password, email: email || "" }),
      }),

    login: (username, password) =>
      request("/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      }),

    logout: () =>
      request("/logout", { method: "POST" }),

    me: () =>
      request("/me"),

    // ─── API Key ───
    getKey: (name, username, password, rateLimit, expiresDays, maxRequests) =>
      request("/get-key", {
        method: "POST",
        body: JSON.stringify({
          name,
          username: username || null,
          password: password || null,
          rate_limit: rateLimit || 100,
          expires_days: expiresDays || null,
          max_requests: maxRequests || null,
        }),
      }),

    listKeys: (apiKey) => {
      // Kalau login (ada token) → pakai Bearer saja
      const hasToken = !!localStorage.getItem("aniwatch_token");
      if (hasToken) return request("/keys", {});

      // Fallback: API key (anonymous)
      if (apiKey) return request("/keys", { headers: { "X-API-Key": apiKey } });
      return request("/keys", {});
    },

    revokeKey: (keyId, apiKey) => {
      const hasToken = !!localStorage.getItem("aniwatch_token");
      if (hasToken) return request(`/keys/${keyId}`, { method: "DELETE" });
      if (apiKey) return request(`/keys/${keyId}`, {
        method: "DELETE",
        headers: { "X-API-Key": apiKey },
      });
      return request(`/keys/${keyId}`, { method: "DELETE" });
    },

    // ─── Data ───
    getAnime: (slug, apiKey) =>
      request(`/share/anime/${slug}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    getEpisode: (number, slug, apiKey) =>
      request(`/share/episode/${number}/${slug}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    getEpisodeList: (slug, apiKey) =>
      request(`/share/episodeid/${slug}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    search: (q, apiKey) =>
      request(`/share/query?q=${encodeURIComponent(q)}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    now: (apiKey) =>
      request("/share/now", {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    // ─── Debug ───
    debug: true,
  };
})();

// ═══════════════════════════════════════════════════════════
//  AUTO LOG SAAT LOAD
// ═══════════════════════════════════════════════════════════
console.log("📡 API Client loaded");
console.log("   Base URL:", API.baseUrl());
console.log("   Debug   :", API.debug);