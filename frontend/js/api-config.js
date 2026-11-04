"use strict";
/* Deployment-owned public origin only; never infer one from Pages or fabricate a backend. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SGNaviApiConfig = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  // Actual free Render HTTPS demo verified by backend owner on 2026-11-04.
  // This is a temporary, EPHEMERAL test service (no persistent quarantine disk).
  // Deploy SHA 635ded120e4dfa3196b6c30b3b162c9d77dd5cf5; never treat as RC1.
  // This is a public endpoint, NOT a credential, token, local IP or example URL.
  const HTTPS_API_ORIGIN = "https://sg-navi-api-free-demo.onrender.com";
  const API_PATHS = new Set(["/api/health", "/api/navigate", "/api/version", "/api/case-types"]);

  function isGitHubPages(location) {
    return Boolean(location && typeof location.hostname === "string" &&
      location.hostname.toLowerCase() === "chu-junjie.github.io" &&
      typeof location.pathname === "string" &&
      (location.pathname === "/SG-Navi" || location.pathname.startsWith("/SG-Navi/")));
  }

  function normalisePublicOrigin(raw) {
    if (typeof raw !== "string" || !raw.trim() || raw.trim() !== raw ||
        /\s/.test(raw) || !/^https:\/\//i.test(raw)) return null;
    try {
      const url = new URL(raw);
      const host = url.hostname.toLowerCase();
      if (url.protocol !== "https:" || url.username || url.password ||
          url.search || url.hash || url.pathname !== "/" ||
          !host.includes(".") || host === "localhost" ||
          host === "example.com" || host.endsWith(".example.com") ||
          [".invalid", ".test", ".example", ".localhost", ".local"].some(s => host.endsWith(s)) ||
          /^\d{1,3}(\.\d{1,3}){3}$/.test(host) || host.includes(":")) return null;
      return url.origin;
    } catch (_) {
      return null;
    }
  }

  function resolve(path, location, origin = HTTPS_API_ORIGIN) {
    if (!API_PATHS.has(path)) throw new Error("Unrecognised API path");
    if (!isGitHubPages(location)) return path; // Local Flask integration: same origin.
    const verified = normalisePublicOrigin(origin);
    return verified ? verified + path : null;
  }

  return Object.freeze({
    resolve, isGitHubPages, normalisePublicOrigin,
    isPublicConfigured: () => Boolean(normalisePublicOrigin(HTTPS_API_ORIGIN))
  });
});
