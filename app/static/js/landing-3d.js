// ============================================================
// Galbay Predictor - 3D Landing Page Hero (Three.js)
// Planet with orbiting gold coins, money-themed
// ============================================================

(function() {
  'use strict';

  function init3D() {
    const canvas = document.getElementById('landing3d');
    if (!canvas) return;

    // WebGL check
    const gl = canvas.getContext('webgl') || canvas.getContext('webgl2') || canvas.getContext('experimental-webgl');
    if (!gl) {
      console.warn('WebGL not supported, falling back to gradient');
      canvas.style.display = 'none';
      return;
    }

    // Check reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Load Three.js from CDN
    const THREE_SCRIPT = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js';
    if (typeof THREE === 'undefined') {
      const script = document.createElement('script');
      script.src = THREE_SCRIPT;
      script.onload = () => startScene(canvas, prefersReducedMotion);
      script.onerror = () => { canvas.style.display = 'none'; };
      document.head.appendChild(script);
    } else {
      startScene(canvas, prefersReducedMotion);
    }
  }

  function startScene(canvas, prefersReducedMotion) {
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? 50 : 200;

    // ========== Scene Setup ==========
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    camera.position.set(0, 0, 8);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: !isMobile,
      powerPreference: 'high-performance',
    });

    function resize() {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (canvas.width !== w || canvas.height !== h) {
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      }
    }
    resize();
    window.addEventListener('resize', resize);

    // ========== Lighting ==========
    const ambient = new THREE.AmbientLight(0xfff5d8, 0.6);
    scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0xfbbf24, 1.5, 30);
    pointLight.position.set(0, 0, 4);
    scene.add(pointLight);

    // ========== Main Planet ==========
    const planetGeometry = new THREE.SphereGeometry(1.8, 64, 64);
    // Procedural gradient material (orange-yellow-green money vibe)
    const planetCanvas = document.createElement('canvas');
    planetCanvas.width = 256;
    planetCanvas.height = 256;
    const pctx = planetCanvas.getContext('2d');
    const grad = pctx.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0, '#16a34a');
    grad.addColorStop(0.4, '#fbbf24');
    grad.addColorStop(0.7, '#ea580c');
    grad.addColorStop(1, '#c2410c');
    pctx.fillStyle = grad;
    pctx.fillRect(0, 0, 256, 256);
    // Add some noise texture
    for (let i = 0; i < 800; i++) {
      const x = Math.random() * 256;
      const y = Math.random() * 256;
      const r = Math.random() * 3;
      pctx.fillStyle = `rgba(${Math.random() < 0.5 ? '255,255,255' : '0,0,0'}, ${Math.random() * 0.08})`;
      pctx.beginPath();
      pctx.arc(x, y, r, 0, Math.PI * 2);
      pctx.fill();
    }
    const planetTexture = new THREE.CanvasTexture(planetCanvas);
    planetTexture.wrapS = THREE.RepeatWrapping;
    const planetMaterial = new THREE.MeshStandardMaterial({
      map: planetTexture,
      roughness: 0.7,
      metalness: 0.1,
    });
    const planet = new THREE.Mesh(planetGeometry, planetMaterial);
    scene.add(planet);

    // ========== Gold Coins (orbiting) ==========
    const coins = [];
    const coinGeometry = new THREE.TorusGeometry(0.28, 0.09, 16, 32);
    const coinMaterial = new THREE.MeshStandardMaterial({
      color: 0xfbbf24,
      metalness: 0.9,
      roughness: 0.2,
      emissive: 0xf59e0b,
      emissiveIntensity: 0.15,
    });

    const coinLabels = ['Rp', '$', '€', '¥'];
    const orbits = [
      { radius: 3.0, speed: 0.4, tilt: 0.3, axis: 'y' },
      { radius: 3.5, speed: 0.3, tilt: -0.4, axis: 'x' },
      { radius: 4.0, speed: 0.25, tilt: 0.6, axis: 'y' },
      { radius: 3.2, speed: -0.35, tilt: -0.5, axis: 'x' },
    ];

    orbits.forEach((orbit, i) => {
      const coin = new THREE.Mesh(coinGeometry, coinMaterial.clone());
      coin.userData.orbit = orbit;
      coin.userData.angle = (i * Math.PI) / 2;
      scene.add(coin);
      coins.push(coin);

      // Add label sprite
      const labelCanvas = document.createElement('canvas');
      labelCanvas.width = 128;
      labelCanvas.height = 128;
      const lctx = labelCanvas.getContext('2d');
      lctx.fillStyle = 'rgba(0,0,0,0)';
      lctx.fillRect(0, 0, 128, 128);
      lctx.font = 'bold 64px Inter, sans-serif';
      lctx.fillStyle = '#1c1917';
      lctx.textAlign = 'center';
      lctx.textBaseline = 'middle';
      lctx.fillText(coinLabels[i] || 'Rp', 64, 64);
      const labelTexture = new THREE.CanvasTexture(labelCanvas);
      const spriteMaterial = new THREE.SpriteMaterial({ map: labelTexture, transparent: true });
      const sprite = new THREE.Sprite(spriteMaterial);
      sprite.scale.set(0.6, 0.6, 0.6);
      coin.add(sprite);
    });

    // ========== Floating Particles ==========
    const particles = new THREE.Group();
    const particleGeometry = new THREE.SphereGeometry(0.04, 6, 6);
    const particleMaterial = new THREE.MeshStandardMaterial({
      color: 0xfbbf24,
      emissive: 0xfbbf24,
      emissiveIntensity: 0.6,
    });
    for (let i = 0; i < particleCount; i++) {
      const p = new THREE.Mesh(particleGeometry, particleMaterial);
      p.position.set(
        (Math.random() - 0.5) * 16,
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 8 - 2
      );
      p.userData.drift = {
        x: (Math.random() - 0.5) * 0.002,
        y: (Math.random() - 0.5) * 0.002,
        z: (Math.random() - 0.5) * 0.001,
      };
      particles.add(p);
    }
    scene.add(particles);

    // ========== Mouse Interaction ==========
    let mouseX = 0, mouseY = 0;
    let targetRotY = 0, targetRotX = 0;
    let isDragging = false;
    let dragStartX = 0, dragStartY = 0;
    let dragRotY = 0, dragRotX = 0;

    canvas.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      if (isDragging) {
        targetRotY = dragRotY + (e.clientX - dragStartX) * 0.005;
        targetRotX = dragRotX + (e.clientY - dragStartY) * 0.005;
      } else {
        mouseX = x;
        mouseY = y;
      }
    });

    canvas.addEventListener('mousedown', (e) => {
      isDragging = true;
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      dragRotY = targetRotY;
      dragRotX = targetRotX;
      canvas.style.cursor = 'grabbing';
    });
    window.addEventListener('mouseup', () => {
      isDragging = false;
      canvas.style.cursor = 'grab';
    });

    // Touch
    let lastTouchX = 0, lastTouchY = 0;
    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        isDragging = true;
        lastTouchX = e.touches[0].clientX;
        lastTouchY = e.touches[0].clientY;
        dragRotY = targetRotY;
        dragRotX = targetRotX;
      }
    }, { passive: true });
    canvas.addEventListener('touchmove', (e) => {
      if (isDragging && e.touches.length === 1) {
        const dx = e.touches[0].clientX - lastTouchX;
        const dy = e.touches[0].clientY - lastTouchY;
        targetRotY = dragRotY + dx * 0.005;
        targetRotX = dragRotX + dy * 0.005;
      }
    }, { passive: true });
    canvas.addEventListener('touchend', () => { isDragging = false; }, { passive: true });

    canvas.style.cursor = 'grab';

    // ========== Click Ripple on Coin ==========
    const raycaster = new THREE.Raycaster();
    const clickMouse = new THREE.Vector2();
    let clickScale = 1;
    let clickTarget = null;

    canvas.addEventListener('click', (e) => {
      const rect = canvas.getBoundingClientRect();
      clickMouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      clickMouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(clickMouse, camera);
      const hits = raycaster.intersectObjects(coins);
      if (hits.length > 0) {
        clickTarget = hits[0].object;
        clickScale = 1.4;
        // Show a small tooltip
        showRipple(e.clientX, e.clientY, '💰 Klik untuk jelajah');
      }
    });

    function showRipple(x, y, msg) {
      const el = document.createElement('div');
      el.className = 'landing-3d-tooltip';
      el.textContent = msg;
      el.style.left = (x - 70) + 'px';
      el.style.top = (y - 40) + 'px';
      document.body.appendChild(el);
      setTimeout(() => el.classList.add('show'), 10);
      setTimeout(() => {
        el.classList.remove('show');
        setTimeout(() => el.remove(), 300);
      }, 1500);
    }

    // ========== Animation Loop ==========
    let isVisible = true;
    const clock = new THREE.Clock();
    document.addEventListener('visibilitychange', () => {
      isVisible = !document.hidden;
    });

    function animate() {
      requestAnimationFrame(animate);
      if (!isVisible) return;

      const t = clock.getElapsedTime();
      const delta = clock.getDelta();

      // Planet rotation
      if (!prefersReducedMotion) {
        planet.rotation.y += 0.002;
        planet.rotation.x = Math.sin(t * 0.3) * 0.05;
      }

      // Mouse parallax (only when not dragging)
      if (!isDragging) {
        targetRotY += (mouseX * 0.4 - targetRotY) * 0.05;
        targetRotX += (-mouseY * 0.3 - targetRotX) * 0.05;
      }
      planet.rotation.y += (targetRotY - planet.rotation.y) * 0.05;
      planet.rotation.x += (targetRotX - planet.rotation.x) * 0.05;

      // Coins orbit
      coins.forEach((coin) => {
        if (!prefersReducedMotion) {
          coin.userData.angle += coin.userData.orbit.speed * 0.01;
        }
        const angle = coin.userData.angle;
        const orbit = coin.userData.orbit;
        const cosA = Math.cos(angle);
        const sinA = Math.sin(angle);
        const tilt = orbit.tilt;
        coin.position.set(
          orbit.radius * cosA,
          Math.sin(tilt) * orbit.radius * sinA,
          orbit.radius * sinA * Math.cos(tilt)
        );
        // Rotate coin to face camera-ish (spin)
        if (!prefersReducedMotion) {
          coin.rotation.z += 0.02;
          coin.rotation.x += 0.01;
        }

        // Click ripple scale animation
        if (coin === clickTarget) {
          clickScale += (1 - clickScale) * 0.1;
          coin.scale.setScalar(clickScale);
        } else {
          coin.scale.setScalar(1);
        }
      });

      // Camera breathing
      if (!prefersReducedMotion) {
        camera.position.z = 8 + Math.sin(t * 0.3) * 0.3;
      }

      // Particles drift
      particles.children.forEach((p) => {
        if (!prefersReducedMotion) {
          p.position.x += p.userData.drift.x;
          p.position.y += p.userData.drift.y;
          p.position.z += p.userData.drift.z;
          if (Math.abs(p.position.x) > 8) p.userData.drift.x *= -1;
          if (Math.abs(p.position.y) > 6) p.userData.drift.y *= -1;
          if (Math.abs(p.position.z) > 5) p.userData.drift.z *= -1;
        }
      });

      resize();
      renderer.render(scene, camera);
    }

    animate();

    // Cleanup
    window.addEventListener('beforeunload', () => {
      renderer.dispose();
      scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
          else obj.material.dispose();
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init3D);
  } else {
    init3D();
  }
})();
