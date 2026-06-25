/* ============================================================
   Galbay Predictor - Scroll Reveal + Topbar Shrink + Chat Attention
   - IntersectionObserver untuk .reveal, .reveal-stagger, .reveal-left, .reveal-right
   - Topbar shrinks setelah 80px scroll
   - Chat bubble attention pulse pada first page load
   - Respects prefers-reduced-motion
   ============================================================ */
(function () {
  'use strict';

  // ---- Detect reduced motion preference ----
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---- 1) Topbar shrink on scroll ----
  const topbar = document.querySelector('.topbar');
  function onScroll() {
    if (!topbar) return;
    if (window.scrollY > 80) {
      topbar.classList.add('scrolled');
    } else {
      topbar.classList.remove('scrolled');
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---- 2) Scroll reveal via IntersectionObserver ----
  let io = null;
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const reveal = (entries, obs) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          obs.unobserve(e.target);
        }
      });
    };
    io = new IntersectionObserver(reveal, {
      root: null,
      rootMargin: '0px 0px -10% 0px',
      threshold: 0.05,
    });
  }

  function observeAll() {
    if (io) {
      document.querySelectorAll('.reveal, .reveal-stagger, .reveal-left, .reveal-right')
        .forEach(el => io.observe(el));
    } else {
      // Fallback: show all immediately
      document.querySelectorAll('.reveal, .reveal-stagger, .reveal-left, .reveal-right')
        .forEach(el => el.classList.add('visible'));
    }
  }
  observeAll();

  // ---- 3) Chat bubble attention (after 1.5s, once per session) ----
  if (!sessionStorage.getItem('chatAttentionShown')) {
    setTimeout(() => {
      const bubble = document.getElementById('chatBubble');
      if (bubble) {
        bubble.classList.add('attention');
        setTimeout(() => bubble.classList.remove('attention'), 1300);
        sessionStorage.setItem('chatAttentionShown', '1');
      }
    }, 1500);
  }

  // ---- 4) Auto-apply .reveal to .page-section + .page-header if not already ----
  // Light-touch: just add reveal class to page-headers (kpi cards, etc already may be styled)
  let addedNew = false;
  document.querySelectorAll('.page-header').forEach(el => {
    if (!el.classList.contains('reveal') && !el.classList.contains('no-reveal')) {
      el.classList.add('reveal');
      addedNew = true;
    }
  });

  // ---- 5) Auto-stagger KPI bars & source cards in groups ----
  document.querySelectorAll('.kpi-bar, .source-grid, .pricing-grid, .multi-source-grid, .kpi-grid').forEach(el => {
    if (!el.classList.contains('reveal-stagger')) {
      el.classList.add('reveal-stagger');
      addedNew = true;
    }
  });

  // Re-observe any elements that got .reveal/.reveal-stagger AFTER initial setup
  if (addedNew) {
    observeAll();
  }

  // ---- 6) Failsafe: auto-show elements already in initial viewport ----
  // Avoids race condition where IO hasn't fired yet on first paint
  requestAnimationFrame(() => {
    setTimeout(() => {
      const vh = window.innerHeight || document.documentElement.clientHeight;
      document.querySelectorAll('.reveal:not(.visible)').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.top < vh && r.bottom > 0) {
          el.classList.add('visible');
          if (io) io.unobserve(el);
        }
      });
    }, 50);
  });

  // ---- 7) Chart re-init on scroll-reveal ----
  // When a chart-wrap becomes visible, re-init or resize any Chart.js inside
  // Fixes issue where charts lower in page render with 0 dimensions
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const chartObserver = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        e.target.classList.add('visible');
        // Find canvas inside the chart-wrap and trigger resize
        const canvas = e.target.querySelector('canvas');
        if (canvas && window.Chart) {
          const chart = window.Chart.getChart && window.Chart.getChart(canvas);
          if (chart) {
            // Chart already exists - just resize
            setTimeout(() => { try { chart.resize(); chart.update('none'); } catch (err) { /* noop */ } }, 50);
          }
        }
        chartObserver.unobserve(e.target);
      });
    }, { root: null, rootMargin: '0px 0px -5% 0px', threshold: 0.1 });

    // Observe all chart-wrap containers that haven't been initialized yet
    document.querySelectorAll('.chart-wrap').forEach(wrap => {
      if (!wrap.classList.contains('visible') && !wrap.dataset.observed) {
        wrap.dataset.observed = '1';
        chartObserver.observe(wrap);
      }
    });
  } else if (window.Chart) {
    // Reduced motion: just mark all chart-wraps as visible immediately
    document.querySelectorAll('.chart-wrap:not(.visible)').forEach(wrap => {
      wrap.classList.add('visible');
    });
  }
  }

  // ---- 8) Failsafe: force chart resize on full page load ----
  // Resize all charts after 1.5s to catch any edge cases
  function resizeAllCharts() {
    if (window.Chart && window.Chart.instances) {
      Object.values(window.Chart.instances).forEach(ch => {
        try {
          ch.resize();
          ch.update('none');
        } catch (e) { /* noop */ }
      });
    }
  }
  window.addEventListener('load', () => {
    [500, 1000, 2000, 3000].forEach(d => setTimeout(resizeAllCharts, d));
  });
  // Also resize on every scroll (debounced) to handle late layout shifts
  let scrollResizeTimer = null;
  window.addEventListener('scroll', () => {
    if (scrollResizeTimer) return;
    scrollResizeTimer = setTimeout(() => {
      scrollResizeTimer = null;
      resizeAllCharts();
    }, 200);
  }, { passive: true });
  // Resize on window resize
  window.addEventListener('resize', () => {
    clearTimeout(window._resizeTimer);
    window._resizeTimer = setTimeout(resizeAllCharts, 100);
  });
})();
