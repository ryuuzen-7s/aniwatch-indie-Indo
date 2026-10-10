/**
 * icons.js — SVG icon library untuk AniWatch Portal.
 * Usage: Icons.key(), Icons.user(), dll.
 */
const Icons = (() => {
  // Base SVG wrapper
  const svg = (paths, viewBox = "0 0 24 24", extra = "") => `
    <svg xmlns="http://www.w3.org/2000/svg"
         viewBox="${viewBox}"
         fill="none"
         stroke="currentColor"
         stroke-width="2"
         stroke-linecap="round"
         stroke-linejoin="round"
         ${extra}>
      ${paths}
    </svg>
  `;

  return {
    // ═══ Brand ═══
    brand: () => svg(`
      <path d="M4 6h16M4 12h16M4 18h10"/>
      <circle cx="19" cy="18" r="2" fill="currentColor"/>
    `),

    // ═══ Navigation ═══
    home: () => svg(`
      <path d="M3 12l9-9 9 9"/>
      <path d="M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10"/>
    `),

    dashboard: () => svg(`
      <rect x="3" y="3" width="7" height="9" rx="1"/>
      <rect x="14" y="3" width="7" height="5" rx="1"/>
      <rect x="14" y="12" width="7" height="9" rx="1"/>
      <rect x="3" y="16" width="7" height="5" rx="1"/>
    `),

    login: () => svg(`
      <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
      <polyline points="10 17 15 12 10 7"/>
      <line x1="15" y1="12" x2="3" y2="12"/>
    `),

    logout: () => svg(`
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    `),

    // ═══ Auth ═══
    key: () => svg(`
      <circle cx="8" cy="15" r="4"/>
      <path d="m10.85 12.15 7.15-7.15"/>
      <path d="M18 5l2 2"/>
      <path d="M15 8l2 2"/>
    `),

    lock: () => svg(`
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    `),

    user: () => svg(`
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    `),

    // ═══ Actions ═══
    plus: () => svg(`
      <line x1="12" y1="5" x2="12" y2="19"/>
      <line x1="5" y1="12" x2="19" y2="12"/>
    `),

    copy: () => svg(`
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    `),

    check: () => svg(`
      <polyline points="20 6 9 17 4 12"/>
    `),

    x: () => svg(`
      <line x1="18" y1="6" x2="6" y2="18"/>
      <line x1="6" y1="6" x2="18" y2="18"/>
    `),

    trash: () => svg(`
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    `),

    download: () => svg(`
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    `),

    external: () => svg(`
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
      <polyline points="15 3 21 3 21 9"/>
      <line x1="10" y1="14" x2="21" y2="3"/>
    `),

    refresh: () => svg(`
      <polyline points="23 4 23 10 17 10"/>
      <polyline points="1 20 1 14 7 14"/>
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/>
      <path d="M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
    `),

    // ═══ Status ═══
    warning: () => svg(`
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    `),

    info: () => svg(`
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="16" x2="12" y2="12"/>
      <line x1="12" y1="8" x2="12.01" y2="8"/>
    `),

    shield: () => svg(`
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    `),

    clock: () => svg(`
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    `),

    zap: () => svg(`
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    `),

    chart: () => svg(`
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    `),

    // ═══ Auto-render ═══
    brandGradient: () => `
      <svg width="0" height="0" style="position:absolute">
        <defs>
          <linearGradient id="brand-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#5b8def"/>
            <stop offset="100%" stop-color="#a855f7"/>
          </linearGradient>
        </defs>
      </svg>
    `,

    renderAll: () => {
      document.querySelectorAll("[data-icon]").forEach((el) => {
        const name = el.getAttribute("data-icon");
        if (Icons[name]) {
          el.innerHTML = Icons[name]();
        }
      });
    },
  };
})();

// Auto-render saat load
document.addEventListener("DOMContentLoaded", () => {
  // Inject gradient
  document.body.insertAdjacentHTML("afterbegin", Icons.brandGradient());
  // Render all icons
  Icons.renderAll();
  console.log("🎨 Icons rendered:",
    document.querySelectorAll("[data-icon]").length);
});

console.log("📚 Icons library loaded. Total icons:",
  Object.keys(Icons).filter(k => typeof Icons[k] === "function").length);
