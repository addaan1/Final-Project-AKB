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
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const reveal = (entries, obs) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          obs.unobserve(e.target);
        }
      });
    };
    const io = new IntersectionObserver(reveal, {
      root: null,
      rootMargin: '0px 0px -10% 0px',
      threshold: 0.12,
    });
    document.querySelectorAll('.reveal, .reveal-stagger, .reveal-left, .reveal-right')
      .forEach(el => io.observe(el));
  } else {
    // Fallback: show all immediately
    document.querySelectorAll('.reveal, .reveal-stagger, .reveal-left, .reveal-right')
      .forEach(el => el.classList.add('visible'));
  }

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
  document.querySelectorAll('.page-header').forEach(el => {
    if (!el.classList.contains('reveal') && !el.classList.contains('no-reveal')) {
      el.classList.add('reveal');
    }
  });

  // ---- 5) Auto-stagger KPI bars & source cards in groups ----
  document.querySelectorAll('.kpi-bar, .source-grid, .pricing-grid, .multi-source-grid').forEach(el => {
    if (!el.classList.contains('reveal-stagger')) {
      el.classList.add('reveal-stagger');
    }
  });
})();
