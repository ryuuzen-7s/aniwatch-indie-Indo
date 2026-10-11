/**
 * api.js — API Client untuk AniWatch Portal
 *
 * Fitur:
 * - Auto-detect base URL
 * - Token via Authorization header (mobile-friendly)
 * - API Key via X-API-Key header
 * - Credentials include (cookie)
 * - Retry pada network error
 * - Handle 200/202/204/401/405/429
 */
const API = (() => {
  // ═══════════════════════════════════════════════════════════
  //  CONFIG
  // ═══════════════════════════════════════════════════════════
  const CONFIG = {
    baseUrl: localStorage.getItem("aniwatch_base_url")
             || window.location.origin,
    timeout: 30000,
    retries: 2,
    retryDelay: 1000,
    debug: true,
  };

  // ═══════════════════════════════════════════════════════════
  //  LOG HELPER
  // ═══════════════════════════════════════════════════════════
  function log(msg, ...args) {
    if (CONFIG.debug) console.log("[API]", msg, ...args);
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
  async function request(path, options = {}) {
    const url = CONFIG.baseUrl + path;
    const method = options.method || "GET";

    const token = localStorage.getItem("aniwatch_token");
    const apiKey = localStorage.getItem("aniwatch_api_key");

    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    // Bearer token (kalau ada)
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = "Bearer " + token;
    }

    // API key (kalau ada & belum di-set)
    if (apiKey && !headers["X-API-Key"]) {
      headers["X-API-Key"] = apiKey;
    }

    log(`${method} ${url}`);
    log("  → Token:", token ? token.slice(0, 20) + "..." : "(none)");
    log("  → API Key:", apiKey ? apiKey.slice(0, 20) + "..." : "(none)");

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);

    // ═══ RETRY LOOP ═══
    let lastError = null;

    for (let attempt = 0; attempt <= CONFIG.retries; attempt++) {
      try {
        const res = await fetch(url, {
          ...options,
          credentials: "include",
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        log(`  ← Status ${res.status}`);

        // Parse JSON
        let data;
        try {
          data = await res.json();
        } catch (e) {
          logError("  ← Bukan JSON:", e.message);
          data = {
            success: false,
            error: {
              code: "NOT_JSON",
              message: "Response bukan JSON",
              status: res.status,
            },
          };
        }

        // Kalau HTTP error & tidak ada error object
        if (!res.ok && !data.error) {
          data.error = {
            code: "HTTP_" + res.status,
            message: res.statusText || "HTTP Error",
            status: res.status,
          };
        }

        // ═══ 401 Unauthorized ═══
        if (res.status === 401 && data.error) {
          const code = data.error.code || "";

          const shouldClear = (
            code === "AUTH_EXPIRED" ||
            code === "TOKEN_INVALID" ||
            code === "SESSION_EXPIRED" ||
            code === "HTTP_401"
          );

          if (shouldClear) {
            warn("Token invalid/expired, clearing...");
            localStorage.removeItem("aniwatch_token");
            localStorage.removeItem("aniwatch_user");
          }

          // Kalau request ke /share/* → redirect ke portal index
          if (path.startsWith("/share/") &&
              !window.location.pathname.includes("/portal/")) {
            const returnUrl = encodeURIComponent(window.location.href);
            window.location.href = `/portal/index.html?return=${returnUrl}`;
          }
        }

        // ═══ 405 Method Not Allowed ═══
        if (res.status === 405) {
          warn("Method tidak diizinkan:", method, path);
        }

        // ═══ 429 Rate Limit ═══
        if (res.status === 429) {
          const retryAfter = res.headers.get("Retry-After") || "60";
          warn(`Rate limit. Retry after ${retryAfter}s`);
          if (data.error) {
            data.error.retry_after = parseInt(retryAfter, 10);
          }
        }

        return data;

      } catch (err) {
        clearTimeout(timeoutId);
        lastError = err;

        if (err.name === "AbortError") {
          logError(`  ← TIMEOUT (${CONFIG.timeout}ms)`);
          return {
            success: false,
            error: { code: "TIMEOUT", message: "Request timeout", status: 408 },
          };
        }

        logError(`  ← Network error (attempt ${attempt + 1}):`, err.message);

        if (attempt < CONFIG.retries) {
          warn(`  → Retry dalam ${CONFIG.retryDelay}ms...`);
          await new Promise((r) => setTimeout(r, CONFIG.retryDelay));
          continue;
        }

        return {
          success: false,
          error: {
            code: "NETWORK",
            message: err.message || "Network error",
            status: 0,
          },
        };
      }
    }

    return {
      success: false,
      error: {
        code: "UNKNOWN",
        message: lastError?.message || "Unknown error",
        status: 0,
      },
    };
  }

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
      const hasToken = !!localStorage.getItem("aniwatch_token");
      if (hasToken) return request("/keys", {});
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

    // ─── Data Anime ───
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

    // ─── Search (dengan 202/204 handling) ───
    search: async (q, apiKey) => {
      const key = apiKey || localStorage.getItem("aniwatch_api_key");
      const data = await request(
        `/share/query?q=${encodeURIComponent(q)}`,
        {
          headers: key ? { "X-API-Key": key } : {},
        }
      );

      // Handle 202 (processing)
      if (data.success && data.data && data.data.status === "processing") {
        const retryAfter = data.data.agent?.retry_after || 30;
        return {
          ...data,
          status: "processing",
          retryAfter,
          pollUrl: data.data.agent?.poll_url,
        };
      }

      // Handle 202 (already processing)
      if (data.success && data.data && data.data.status === "already_processing") {
        const retryAfter = data.data.agent?.retry_after || 15;
        return {
          ...data,
          status: "already_processing",
          retryAfter,
          pollUrl: data.data.agent?.poll_url,
        };
      }

      // Handle 204 (no content)
      if (!data.success && data.error && data.error.code === "NO_RESULT") {
        return {
          ...data,
          status: "not_found",
        };
      }

      // Handle 200 (success)
      if (data.success && data.data && data.data.results) {
        return {
          ...data,
          status: "ready",
        };
      }

      return data;
    },

    // ─── Now ───
    now: (apiKey) =>
      request("/share/now", {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    // ─── Season ───
    season: (season, apiKey) =>
      request(`/share/season/${season}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    // ─── Poster ───
    getPoster: (slug, apiKey) =>
      request(`/share/posterid/${slug}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    // ─── Report ───
    reportError: (slug, body, apiKey) =>
      request(`/share/errorid/${slug}`, {
        method: "POST",
        headers: apiKey ? { "X-API-Key": apiKey } : {},
        body: JSON.stringify(body),
      }),

    // ─── Scrape Status ───
    scrapeStatus: (slug, apiKey) =>
      request(`/share/scrape-status/${slug}`, {
        headers: apiKey ? { "X-API-Key": apiKey } : {},
      }),

    scrapeJobs: (apiKey) =>
      request("/share/scrape-jobs", {
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