// ============================================================
// Galbay Predictor - CSS-Only Animated Hero
// Floating coin stack + sparkle particles (no Three.js)
// ============================================================

(function() {
  'use strict';

  function init() {
    const root = document.getElementById('hero3d');
    if (!root) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      // Skip animation, show static
      return;
    }
    spawnSparkles(root);
    initMouseParallax(root);
  }

  function spawnSparkles(root) {
    const layer = root.querySelector('.hero-sparkles');
    if (!layer) return;
    const count = window.innerWidth < 768 ? 30 : 60;
    for (let i = 0; i < count; i++) {
      const s = document.createElement('span');
      s.className = 'hero-sparkle';
      const size = 2 + Math.random() * 4;
      s.style.cssText = `
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        width: ${size}px; height: ${size}px;
        animation-delay: ${Math.random() * 5}s;
        animation-duration: ${3 + Math.random() * 4}s;
      `;
      layer.appendChild(s);
    }
  }

  function initMouseParallax(root) {
    const coins = root.querySelectorAll('.hero-coin');
    if (!coins.length) return;
    let tx = 0, ty = 0;
    let cx = 0, cy = 0;
    document.addEventListener('mousemove', (e) => {
      const w = window.innerWidth, h = window.innerHeight;
      tx = (e.clientX / w - 0.5) * 2;
      ty = (e.clientY / h - 0.5) * 2;
    });
    function tick() {
      cx += (tx - cx) * 0.08;
      cy += (ty - cy) * 0.08;
      coins.forEach((coin, i) => {
        const depth = (i + 1) * 6;
        coin.style.setProperty('--mx', (cx * depth) + 'px');
        coin.style.setProperty('--my', (cy * depth) + 'px');
      });
      requestAnimationFrame(tick);
    }
    tick();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
