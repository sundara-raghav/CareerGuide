/**
 * main.js — global utilities and micro-interactions
 */

// ── Analytics event helper ───────────────────────────────────────────────────
window.trackEvent = function (event, properties = {}) {
  try {
    // Send to /analytics/api/event if available
    fetch('/analytics/api/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, properties, ts: Date.now() }),
    }).catch(() => {}); // fire and forget
  } catch {}
};

// ── Intersection Observer for lazy animations ────────────────────────────────
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.1 }
);

document.querySelectorAll('[data-observe]').forEach(el => observer.observe(el));

// ── Tooltip utility ──────────────────────────────────────────────────────────
function initTooltips() {
  document.querySelectorAll('[data-tooltip]').forEach(el => {
    el.addEventListener('mouseenter', e => {
      const tip = document.createElement('div');
      tip.id = 'tooltip';
      tip.className = 'fixed z-[9999] bg-gray-800 text-white text-xs px-2 py-1 rounded-lg pointer-events-none shadow-lg max-w-[200px]';
      tip.textContent = el.dataset.tooltip;
      document.body.appendChild(tip);

      const rect = el.getBoundingClientRect();
      tip.style.top = (rect.top - tip.offsetHeight - 8 + window.scrollY) + 'px';
      tip.style.left = (rect.left + rect.width / 2 - tip.offsetWidth / 2) + 'px';
    });
    el.addEventListener('mouseleave', () => {
      document.getElementById('tooltip')?.remove();
    });
  });
}

// ── Copy to clipboard ────────────────────────────────────────────────────────
window.copyToClipboard = function (text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = '✓ Copied!';
    btn.classList.add('text-emerald-400');
    setTimeout(() => { btn.textContent = original; btn.classList.remove('text-emerald-400'); }, 2000);
  });
};

// ── API helper ───────────────────────────────────────────────────────────────
window.api = {
  get: async (url) => {
    const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  post: async (url, body) => {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
};

// ── Service Worker (offline support) ─────────────────────────────────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/sw.js').catch(() => {});
  });
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTooltips();
});
