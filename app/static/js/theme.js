// ============================================================
// Galbay Predictor - Theme Toggle (Light / Dark)
// Default: light (trust-first). Persist via localStorage.
// ============================================================
(function () {
  'use strict';

  const STORAGE_KEY = 'galbay_theme';

  function getStoredTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) { /* noop */ }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const btn = document.getElementById('themeToggle');
    if (btn) {
      btn.setAttribute('aria-label', theme === 'light' ? 'Aktifkan dark mode' : 'Aktifkan light mode');
      const icon = btn.querySelector('.theme-icon');
      if (icon) {
        icon.textContent = theme === 'light' ? '☾' : '☀';
      }
    }
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    applyTheme(next);
    setStoredTheme(next);
  }

  // Init: respect stored preference, else default to light
  function init() {
    const stored = getStoredTheme();
    const theme = (stored === 'dark' || stored === 'light') ? stored : 'light';
    applyTheme(theme);

    const btn = document.getElementById('themeToggle');
    if (btn) {
      btn.addEventListener('click', toggleTheme);
    }
  }

  // Run after DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
