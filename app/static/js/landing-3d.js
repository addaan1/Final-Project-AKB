// ============================================================
// Galbay Predictor - Premium Animated Hero (CSS + JS only, no Three.js)
// Features: 8 floating coins · 120 sparkles · mouse trail (3 layers) ·
// central pulsing orb · mouse parallax
// ============================================================

(function() {
  'use strict';

  function init() {
    const root = document.getElementById('hero3d');
    if (!root) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    spawnSparkles(root);
    spawnTrailLayer(root);
    initMouseParallax(root);
    initTrail(root);
    initCentralOrb(root);
  }

  // 120 small background sparkles (twinkling)
  function spawnSparkles(root) {
    const layer = root.querySelector('.hero-sparkles');
    if (!layer) return;
    const isMobile = window.innerWidth < 768;
    const count = isMobile ? 50 : 120;
    const palette = ['#fbbf24', '#fde68a', '#fef3c7', '#a3e635', '#fb923c'];
    for (let i = 0; i < count; i++) {
      const s = document.createElement('span');
      s.className = 'hero-sparkle';
      const size = 2 + Math.random() * 5;
      const color = palette[Math.floor(Math.random() * palette.length)];
      s.style.cssText = `
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        width: ${size}px; height: ${size}px;
        background: radial-gradient(circle, ${color} 0%, transparent 70%);
        animation-delay: ${Math.random() * 5}s;
        animation-duration: ${2.5 + Math.random() * 4}s;
        opacity: 0;
      `;
      layer.appendChild(s);
    }
  }

  // Trail layer DOM
  function spawnTrailLayer(root) {
    if (!root.querySelector('.hero-trail')) {
      const t = document.createElement('div');
      t.className = 'hero-trail';
      t.setAttribute('aria-hidden', 'true');
      root.appendChild(t);
    }
  }

  // Mouse parallax for coin positions
  function initMouseParallax(root) {
    const coins = root.querySelectorAll('.hero-coin');
    if (!coins.length) return;
    let tx = 0, ty = 0;
    let cx = 0, cy = 0;
    let rafId = null;
    document.addEventListener('mousemove', (e) => {
      const w = window.innerWidth, h = window.innerHeight;
      tx = (e.clientX / w - 0.5) * 2;
      ty = (e.clientY / h - 0.5) * 2;
    });
    function tick() {
      cx += (tx - cx) * 0.06;
      cy += (ty - cy) * 0.06;
      coins.forEach((coin, i) => {
        const depth = (i + 1) * 5;
        coin.style.setProperty('--mx', (cx * depth) + 'px');
        coin.style.setProperty('--my', (cy * depth) + 'px');
      });
      rafId = requestAnimationFrame(tick);
    }
    if (rafId) cancelAnimationFrame(rafId);
    tick();
  }

  // 3-layer mouse trail (orb + dust + ring)
  function initTrail(root) {
    const trailLayer = root.querySelector('.hero-trail');
    if (!trailLayer) return;
    const heroRect = root.getBoundingClientRect();
    let lastSpawn = 0;
    const SPAWN_INTERVAL = 28; // ms between particle spawns
    const isCoarse = window.matchMedia('(pointer: coarse)').matches;
    if (isCoarse) return; // disable on touch

    document.addEventListener('mousemove', (e) => {
      const now = performance.now();
      if (now - lastSpawn < SPAWN_INTERVAL) return;
      lastSpawn = now;

      // Only spawn if mouse is in hero
      const rect = root.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right ||
          e.clientY < rect.top || e.clientY > rect.bottom) return;

      // Layer 1: bright glow orb (rare, big)
      if (Math.random() < 0.25) {
        spawnOrb(trailLayer, e.clientX, e.clientY);
      }
      // Layer 2: small dust (frequent)
      if (Math.random() < 0.7) {
        spawnDust(trailLayer, e.clientX, e.clientY);
      }
      // Layer 3: ring ripple (rare)
      if (Math.random() < 0.08) {
        spawnRing(trailLayer, e.clientX, e.clientY);
      }
    });
  }

  function spawnOrb(layer, x, y) {
    const el = document.createElement('div');
    el.className = 'trail-orb';
    const size = 12 + Math.random() * 10;
    el.style.cssText = `left:${x - size/2}px;top:${y - size/2}px;width:${size}px;height:${size}px;`;
    layer.appendChild(el);
    setTimeout(() => el.remove(), 1100);
  }

  function spawnDust(layer, x, y) {
    const el = document.createElement('div');
    el.className = 'trail-dust';
    const size = 4 + Math.random() * 4;
    const dx = (Math.random() - 0.5) * 24;
    const dy = (Math.random() - 0.5) * 24;
    el.style.cssText = `left:${x}px;top:${y}px;--dx:${dx}px;--dy:${dy}px;width:${size}px;height:${size}px;`;
    layer.appendChild(el);
    setTimeout(() => el.remove(), 900);
  }

  function spawnRing(layer, x, y) {
    const el = document.createElement('div');
    el.className = 'trail-ring';
    el.style.cssText = `left:${x}px;top:${y}px;`;
    layer.appendChild(el);
    setTimeout(() => el.remove(), 800);
  }

  // Central pulsing orb (always visible focal point)
  function initCentralOrb(root) {
    let orb = root.querySelector('.hero-orb');
    if (orb) return;
    orb = document.createElement('div');
    orb.className = 'hero-orb';
    orb.setAttribute('aria-hidden', 'true');
    orb.innerHTML = '<span class="hero-orb-core"></span><span class="hero-orb-ring"></span>';
    root.appendChild(orb);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
