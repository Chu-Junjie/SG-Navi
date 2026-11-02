"use strict";
/* Presentation-only evidence filtering. Metadata is not proof of legal eligibility. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SGNaviVerifiedSources = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const isNonBlank = value => typeof value === "string" && /\S/.test(value);

  function safeUrl(value) {
    if (!isNonBlank(value) || value !== value.trim() || /\s/.test(value) ||
        !/^https?:\/\//i.test(value)) return null;
    try {
      const parsed = new URL(value);
      const host = parsed.hostname.toLowerCase();
      if (!["https:", "http:"].includes(parsed.protocol) || !host ||
          parsed.username || parsed.password ||
          host === "localhost" || host === "0.0.0.0" ||
          host === "127.0.0.1" || host === "::1" || host.includes(":") ||
          host === "example.com" || host.endsWith(".example.com") ||
          [".invalid", ".test", ".example", ".localhost", ".local"].some(suffix => host.endsWith(suffix)) ||
          !host.includes(".")) return null;
      // Do not turn backend-controlled source metadata into local/private browser navigation.
      const octets = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
      if (octets) {
        const values = octets.slice(1).map(Number);
        if (values.some(n => n > 255)) return null;
        const a = values[0], b = values[1];
        if (a === 0 || a === 10 || a === 127 || a >= 224 ||
            (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) ||
            (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127)) return null;
      }
      return parsed.href;
    } catch (_) {
      return null;
    }
  }

  function selectVerifiedSources(response) {
    // All-or-nothing. Mixed, duplicate, mock or stale evidence is not displayed.
    if (!response || !["REFER_TO_OFFICIAL", "SUPPORTED_PATH"].includes(response.status) ||
        !isNonBlank(response.source_version) ||
        /^mock/i.test(response.source_version.trim()) ||
        !Array.isArray(response.evidence) || !response.evidence.length) return null;
    if (response.status === "REFER_TO_OFFICIAL" && response.action_card !== null) return null;
    const selected = [];
    const ids = new Set();
    for (const record of response.evidence) {
      if (!record || !isNonBlank(record.evidence_id) ||
          !isNonBlank(record.source_id) ||
          record.evidence_id !== record.evidence_id.trim() ||
          ids.has(record.evidence_id) ||
          record.review_status !== "verified" ||
          record.source_version !== response.source_version ||
          !Array.isArray(record.rule_ids) || !record.rule_ids.length ||
          record.rule_ids.some(id => !isNonBlank(id)) ||
          new Set(record.rule_ids).size !== record.rule_ids.length) return null;
      const href = safeUrl(record.url);
      if (!href) return null;
      ids.add(record.evidence_id);
      selected.push({ evidence_id: record.evidence_id, source_id: record.source_id,
        source_version: record.source_version, review_status: record.review_status, href });
    }
    if (response.status === "SUPPORTED_PATH") {
      const citations = response.action_card?.citations;
      if (!Array.isArray(citations) || !citations.length ||
          citations.some(id => !ids.has(id)) ||
          new Set(citations).size !== citations.length) return null;
      const byId = new Map(selected.map(source => [source.evidence_id, source]));
      return citations.map(id => byId.get(id));
    }
    return selected;
  }

  function renderReferralSources(container, response, doc) {
    container.replaceChildren();
    if (response?.status !== "REFER_TO_OFFICIAL") return false;
    const sources = selectVerifiedSources(response);
    if (!sources || !sources.length) {
      const message = doc.createElement("p");
      message.textContent = "Needs verification — no valid source references are available.";
      container.appendChild(message);
      return false;
    }
    const list = doc.createElement("ul");
    list.className = "source-list";
    for (const source of sources) {
      const item = doc.createElement("li");
      const link = doc.createElement("a");
      link.textContent = source.source_id + " — open source reference";
      link.href = source.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      item.appendChild(link);
      const meta = doc.createElement("p");
      meta.className = "source-meta";
      meta.textContent = "Evidence ID: " + source.evidence_id +
        " · Source version: " + source.source_version +
        " · Review status: " + source.review_status;
      item.appendChild(meta);
      list.appendChild(item);
    }
    container.appendChild(list);
    return true;
  }
  return { safeUrl, selectVerifiedSources, renderReferralSources };
});
