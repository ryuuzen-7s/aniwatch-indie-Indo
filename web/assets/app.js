/**
 * app.js — Logic utama Portal AniWatch
 */

// ═══════════════════════════════════════════════════════════
//  UTILS
// ═══════════════════════════════════════════════════════════
const $ = (id) => document.getElementById(id);

function showAlert(msg, type = "info", containerId = "alert") {
  const el = $(containerId);
  if (!el) return;
  el.className = "alert alert-" + type + " show";
  el.textContent = msg;
  setTimeout(() => el.classList.remove("show"), 6000);
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    // Fallback
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      return true;
    } catch (err) {
      return false;
    }
  }
}

function formatDate(iso) {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    return d.toLocaleString("id-ID", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch (e) {
    return iso;
  }
}

function timeUntil(iso) {
  if (!iso) return "∞";
  try {
    const now = new Date();
    const dt = new Date(iso);
    const diff = dt - now;
    if (diff < 0) return "expired";
    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    if (days > 0) return `${days}d ${hours}h`;
    const minutes = Math.floor((diff % 3600000) / 60000);
    return `${hours}h ${minutes}m`;
  } catch (e) {
    return "-";
  }
}

// ═══════════════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════════════
const state = {
  apiKey: localStorage.getItem("aniwatch_api_key") || "",
  token: localStorage.getItem("aniwatch_token") || "",
  user: JSON.parse(localStorage.getItem("aniwatch_user") || "null"),
};

function saveState() {
  if (state.apiKey) {
    localStorage.setItem("aniwatch_api_key", state.apiKey);
  } else {
    localStorage.removeItem("aniwatch_api_key");
  }
  if (state.token) {
    localStorage.setItem("aniwatch_token", state.token);
  } else {
    localStorage.removeItem("aniwatch_token");
  }
  if (state.user) {
    localStorage.setItem("aniwatch_user", JSON.stringify(state.user));
  } else {
    localStorage.removeItem("aniwatch_user");
  }
}

// ═══════════════════════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════════════════════
function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      tab.classList.add("active");
      const content = $("tab-" + target);
      if (content) content.classList.add("active");
    });
  });
}

// ═══════════════════════════════════════════════════════════
//  QUICK KEY (index.html)
// ═══════════════════════════════════════════════════════════
const QUICK_CONFIG = {
  rateLimit: 18,
  maxRequests: 130,
  expiresHours: 24,
  storageKey: "aniwatch_quick_key_used",
};

function isQuickUsed() {
  const raw = localStorage.getItem(QUICK_CONFIG.storageKey);
  if (!raw) return false;
  try {
    const data = JSON.parse(raw);
    const created = new Date(data.createdAt).getTime();
    const hoursElapsed = (Date.now() - created) / 3600000;
    if (hoursElapsed >= QUICK_CONFIG.expiresHours) {
      localStorage.removeItem(QUICK_CONFIG.storageKey);
      return false;
    }
    return data;
  } catch (e) {
    return false;
  }
}

function markQuickUsed(apiKey, keyId, keyInfo) {
  localStorage.setItem(QUICK_CONFIG.storageKey, JSON.stringify({
    apiKey, keyId, keyInfo,
    createdAt: new Date().toISOString(),
  }));
}

function renderQuickState() {
  const form = $("form-quick");
  const result = $("key-result");
  const blocked = $("quick-blocked");
  if (!form || !result) return;

  const used = isQuickUsed();

  if (!used) {
    form.style.display = "block";
    if (blocked) blocked.style.display = "none";
    result.style.display = "none";
    return;
  }

  form.style.display = "none";
  if (blocked) blocked.style.display = "block";
  result.style.display = "block";

  const keyVal = $("key-value");
  if (keyVal) keyVal.textContent = used.apiKey;

  const info = $("key-info");
  if (info) {
    const created = new Date(used.createdAt).getTime();
    const expiresAt = created + (QUICK_CONFIG.expiresHours * 3600000);
    const remaining = Math.max(0, expiresAt - Date.now());
    const hours = Math.floor(remaining / 3600000);
    const minutes = Math.floor((remaining % 3600000) / 60000);

    info.innerHTML =
      `<div>Dibuat: <b>${new Date(used.createdAt).toLocaleString("id-ID")}</b></div>` +
      `<div>Sisa: <b>${hours}j ${minutes}m</b></div>`;
  }
}

async function submitQuickKey(e) {
  e.preventDefault();

  if (isQuickUsed()) {
    showAlert("❌ Anda sudah buat quick key", "error", "quick-alert");
    return;
  }

  const btn = $("btn-quick");
  const name = $("quick-name") ? $("quick-name").value.trim() : "quick-key";
  const finalName = "[QUICK] " + (name || "app");

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Membuat...';
  }

  try {
    const data = await API.getKey(
      finalName,
      null, null,
      QUICK_CONFIG.rateLimit,
      1, // 1 hari
      QUICK_CONFIG.maxRequests
    );

    if (!data.success) {
      throw new Error(data.error?.message || "Gagal");
    }

    markQuickUsed(data.data.key, data.data.info.id, data.data.info);

    state.apiKey = data.data.key;
    saveState();

    renderQuickState();
    showAlert("✅ Quick key dibuat!", "success", "quick-alert");

  } catch (err) {
    showAlert("❌ " + err.message, "error", "quick-alert");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "🔑 Buat Quick Key";
    }
  }
}

// ═══════════════════════════════════════════════════════════
//  REGISTER (login.html)
// ═══════════════════════════════════════════════════════════
async function submitRegister(e) {
  e.preventDefault();

  const btn = e.target.querySelector("button[type=submit]");
  const username = $("reg-username") ? $("reg-username").value.trim() : "";
  const password = $("reg-password") ? $("reg-password").value : "";
  const email = $("reg-email") ? $("reg-email").value.trim() : "";

  if (!username || !password) {
    showAlert("❌ Username & password wajib", "error", "reg-alert");
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Mendaftar...';
  }

  try {
    const data = await API.register(username, password, email);
    if (!data.success) {
      throw new Error(data.error?.message || "Gagal daftar");
    }

    showAlert("✅ Registrasi berhasil! Silakan login.", "success", "reg-alert");

    setTimeout(() => {
      const loginTab = document.querySelector('.tab[data-tab="login"]');
      if (loginTab) loginTab.click();
      const loginInput = $("login-username");
      if (loginInput) loginInput.value = username;
    }, 1200);

  } catch (err) {
    showAlert("❌ " + err.message, "error", "reg-alert");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "📝 Daftar";
    }
  }
}

// ═══════════════════════════════════════════════════════════
//  LOGIN (login.html)
// ═══════════════════════════════════════════════════════════
async function submitLogin(e) {
  e.preventDefault();

  const btn = e.target.querySelector("button[type=submit]");
  const username = $("login-username") ? $("login-username").value.trim() : "";
  const password = $("login-password") ? $("login-password").value : "";

  if (!username || !password) {
    showAlert("❌ Username & password wajib", "error", "login-alert");
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Login...';
  }

  try {
    const data = await API.login(username, password);
    console.log("📦 Login response:", data);

    if (!data.success) {
      throw new Error(data.error?.message || "Login gagal");
    }

    console.log("🔍 data.data:", data.data);
    console.log("🔍 token:", data.data?.token);
    console.log("🔍 user:", data.data?.user);

    const token = data.data?.token || data.token || data.data?.session_token;
    const user = data.data?.user || data.user;

    if (!token) {
      console.error("❌ Token tidak ada di response!");
      showAlert("❌ Server tidak return token", "error", "login-alert");
      return;
    }

    state.token = token;
    state.user = user;
    localStorage.setItem("aniwatch_token", token);
    if (user) {
      localStorage.setItem("aniwatch_user", JSON.stringify(user));
    }

    console.log("✅ Token tersimpan:", token.slice(0, 30) + "...");
    console.log("✅ User tersimpan:", user?.username);
    console.log("🔍 Verify token:", localStorage.getItem("aniwatch_token")?.slice(0, 30));

    saveState();

    console.log("✅ Login sukses, redirect...");
    showAlert("✅ Login berhasil!", "success", "login-alert");

    setTimeout(() => {
      window.location.href = "/portal/dashboard.html";
    }, 1500);

  } catch (err) {
    console.error("❌ Login error:", err);
    showAlert("❌ " + err.message, "error", "login-alert");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "🔓 Login";
    }
  }
}


// ═══════════════════════════════════════════════════════════
//  DASHBOARD (dashboard.html)
// ═══════════════════════════════════════════════════════════
async function loadKeys() {
  const list = $("keys-list");
  if (!list) return;

  const apiKey = localStorage.getItem("aniwatch_api_key");

  // Kalau tidak ada API key, tapi ada token → tetap bisa lihat list
  if (!apiKey && !state.token) {
    list.innerHTML = `
      <div class="empty">
        <div class="icon">🔑</div>
        <p>Belum ada API key di sesi ini. Buat satu di atas.</p>
      </div>`;
    return;
  }

  try {
    const data = await API.listKeys(apiKey);

    if (!data.success) {
      throw new Error(data.error?.message || "Gagal load keys");
    }

    const keys = data.data || [];

    if (keys.length === 0) {
      list.innerHTML = `
        <div class="empty">
          <div class="icon">🔑</div>
          <p>Belum ada API key.</p>
        </div>`;
      return;
    }

    const html = keys.map((k) => {
      // Status
      let statusClass = "active";
      let statusText = "Active";
      if (!k.is_active) {
        statusClass = "revoked";
        statusText = "Revoked";
      } else if (k.expires_at && new Date(k.expires_at) < new Date()) {
        statusClass = "expired";
        statusText = "Expired";
      }

      return `
        <div class="key-item">
          <div class="header-row">
            <div class="key-name">
              ${k.name || "(no name)"}
              <span class="badge-status ${statusClass}">${statusText}</span>
              ${k.role === "admin" ? '<span class="badge-role admin">admin</span>' : ''}
            </div>
            <div class="key-prefix">${k.key_prefix}...</div>
          </div>
          <div class="meta">
            <div class="item">
              <span class="label">Limit:</span>
              <span class="value">${k.rate_limit} req/menit</span>
            </div>
            <div class="item">
              <span class="label">Used:</span>
              <span class="value">${k.request_count || 0}</span>
            </div>
            <div class="item">
              <span class="label">Expires:</span>
              <span class="value">${k.expires_at ? timeUntil(k.expires_at) : "∞"}</span>
            </div>
            <div class="item">
              <button class="tiny secondary" onclick="revokeKey(${k.id})">
                🗑️ Revoke
              </button>
            </div>
          </div>
        </div>
      `;
    }).join("");

    list.innerHTML = html;

  } catch (err) {
    list.innerHTML = `
      <div class="empty">
        <div class="icon">⚠️</div>
        <p>Error: ${err.message}</p>
      </div>`;
  }
}

async function createKey() {
  const btn = $("btn-create-key");
  const name = $("new-key-name") ? $("new-key-name").value.trim() : "default";
  const limit = $("new-key-limit") ? parseInt($("new-key-limit").value) : 100;

  if (btn) {
    btn.disabled = true;
    btn.textContent = "Membuat...";
  }

  try {
    const data = await API.getKey(name, null, null, limit, 90);

    if (!data.success) {
      throw new Error(data.error?.message || "Gagal");
    }

    localStorage.setItem("aniwatch_api_key", data.data.key);

    showAlert("✅ Key dibuat! Copy: " + data.data.key, "success", "keys-alert");
    await copyToClipboard(data.data.key);

    await loadKeys();
    if ($("new-key-name")) $("new-key-name").value = "";

  } catch (err) {
    showAlert("❌ " + err.message, "error", "keys-alert");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "➕ Buat";
    }
  }
}

async function revokeKey(keyId) {
  if (!confirm("Revoke key ini?")) return;

  const apiKey = localStorage.getItem("aniwatch_api_key");

  try {
    const data = await API.revokeKey(keyId, apiKey);
    if (!data.success) {
      throw new Error(data.error?.message || "Gagal revoke");
    }
    showAlert("✅ Key di-revoke", "success", "keys-alert");
    await loadKeys();
  } catch (err) {
    showAlert("❌ " + err.message, "error", "keys-alert");
  }
}

async function doLogout() {
  if (!confirm("Logout dari akun ini?")) return;

  try {
    await API.logout();
  } catch (e) {
    // ignore
  }

  localStorage.removeItem("aniwatch_user");
  localStorage.removeItem("aniwatch_api_key");
  localStorage.removeItem("aniwatch_token");

  window.location.href = "/portal/index.html";
}

// ═══════════════════════════════════════════════════════════
//  INIT — Dipanggil saat DOM ready
// ═══════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  // Tabs
  initTabs();

  // Bind form (jika ada)
  const formQuick = $("form-quick");
  const formRegister = $("form-register");
  const formLogin = $("form-login");

  if (formQuick) formQuick.addEventListener("submit", submitQuickKey);
  if (formRegister) formRegister.addEventListener("submit", submitRegister);
  if (formLogin) formLogin.addEventListener("submit", submitLogin);

  // Copy button
  const btnCopy = $("btn-copy-key");
  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      const key = $("key-value") ? $("key-value").textContent : "";
      copyToClipboard(key).then((ok) => {
        showAlert(ok ? "✅ Dicopy!" : "❌ Gagal copy",
                  ok ? "success" : "error", "quick-alert");
      });
    });
  }

  // Dashboard specific
  const welcome = $("welcome");
  if (welcome && state.user) {
    welcome.textContent = `Selamat datang, ${state.user.username}!`;
    if ($("user-name")) $("user-name").textContent = state.user.username;
    if ($("user-role")) $("user-role").textContent = state.user.role;
  }

  // Dashboard: redirect kalau belum login
  if ($("keys-list") && !state.user) {
    console.log("🔒 Belum login, redirect...");
    window.location.href = "/portal/login.html";
    return;
  }

  // Dashboard: load keys
  if ($("keys-list")) loadKeys();

  // Bind create key button
  const btnCreate = $("btn-create-key");
  if (btnCreate) btnCreate.addEventListener("click", createKey);

  // Bind logout
  const btnLogout = $("btn-logout");
  if (btnLogout) {
    btnLogout.addEventListener("click", (e) => {
      e.preventDefault();
      doLogout();
    });
  }

  // Quick state
  if ($("form-quick")) renderQuickState();

  console.log("🎌 Portal loaded. User:", state.user ? state.user.username : "anonymous");
});

// Expose globally
window.revokeKey = revokeKey;
window.doLogout = doLogout;