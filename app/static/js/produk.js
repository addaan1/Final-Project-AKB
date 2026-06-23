// ============================================================
// Galbay Predictor - Produk Page Logic
// Menggunakan API endpoints (siap untuk swap ke ML model)
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  initSkorForm();
  initSimulasi();
  initWaitlist();
  initSmoothScroll();
});

// ============================================================
// SKOR RISIKO GALBAY — Panggil /api/score
// ============================================================
function initSkorForm() {
  const form = document.getElementById('skorForm');
  if (!form) return;

  // Slider live update
  const slider = document.getElementById('selfrewardSlider');
  const sliderValue = document.getElementById('selfrewardValue');
  const sliderLabel = document.getElementById('selfrewardLabel');
  if (slider && sliderValue) {
    slider.addEventListener('input', () => {
      sliderValue.textContent = slider.value;
      if (sliderLabel) {
        if (slider.value <= 3) sliderLabel.textContent = 'Rendah';
        else if (slider.value <= 6) sliderLabel.textContent = 'Sedang';
        else sliderLabel.textContent = 'Tinggi';
      }
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type=submit]');
    setLoading(submitBtn, true);

    try {
      const fd = new FormData(form);
      const apps = fd.getAll('apps');
      const payload = {
        apps: apps,
        utang: fd.get('utang') || '0',
        selfreward: parseInt(fd.get('selfreward') || '3', 10),
        telat: fd.get('telat') || '0',
        dc: fd.get('dc') || '0',
        feeling: fd.get('feeling') || '0',
      };
      const resp = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await resp.json();
      renderSkorResult(result);
    } catch (err) {
      console.error('Score API error:', err);
      renderSkorError();
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

function renderSkorResult(result) {
  const container = document.getElementById('skorResult');
  if (!container) return;

  const { score, category, category_label, description, recommendations, model_version } = result;
  const circumference = 2 * Math.PI * 86;
  const offset = circumference - (score / 100) * circumference;

  container.innerHTML = `
    <div class="skor-display">
      <div class="skor-circle" style="--p: ${score}%;">
        <svg viewBox="0 0 200 200" class="skor-svg">
          <circle cx="100" cy="100" r="86" stroke="rgba(155,93,229,0.15)" stroke-width="12" fill="none"/>
          <circle cx="100" cy="100" r="86" stroke="currentColor" stroke-width="12" fill="none"
            stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
            stroke-linecap="round" transform="rotate(-90 100 100)"/>
        </svg>
        <div class="skor-number" data-target="${score}">0</div>
        <div class="skor-label">/ 100</div>
      </div>
      <div class="skor-category ${category}">${category_label}</div>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:24px;">${description}</p>
      <div class="skor-recs">
        <h4>3 Rekomendasi Utama</h4>
        ${recommendations.map((rec, i) => `
          <div class="skor-rec-item">
            <div class="skor-rec-num">${i + 1}</div>
            <div>${rec}</div>
          </div>
        `).join('')}
      </div>
      <div class="skor-version">Model: ${model_version}</div>
    </div>
  `;

  // Animate counter
  const numEl = container.querySelector('.skor-number');
  if (numEl) animateCounter(numEl, parseInt(numEl.dataset.target, 10));

  // Confetti for aman category
  if (category === 'aman') {
    setTimeout(() => triggerConfetti(), 300);
  }
}

function renderSkorError() {
  const container = document.getElementById('skorResult');
  if (!container) return;
  container.innerHTML = `
    <div class="skor-placeholder">
      <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <p>Terjadi kesalahan. Coba lagi.</p>
    </div>
  `;
}

// ============================================================
// SIMULASI CICILAN — Panggil /api/simulate
// ============================================================
function initSimulasi() {
  const nominal = document.getElementById('nominal');
  const bunga = document.getElementById('bunga');
  const tenor = document.getElementById('tenor');
  const admin = document.getElementById('admin');
  if (!nominal || !bunga || !tenor || !admin) return;

  const bungaValue = document.getElementById('bungaValue');
  if (bungaValue) {
    bunga.addEventListener('input', () => { bungaValue.textContent = bunga.value; });
  }

  let debounce;
  [nominal, bunga, tenor, admin].forEach(el => {
    el.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(updateSimulasi, 200);
    });
    el.addEventListener('change', updateSimulasi);
  });
  updateSimulasi();
}

async function updateSimulasi() {
  const payload = {
    nominal: parseFloat(document.getElementById('nominal').value) || 0,
    bunga_pct: parseFloat(document.getElementById('bunga').value) || 0,
    tenor: parseInt(document.getElementById('tenor').value) || 1,
    admin: parseFloat(document.getElementById('admin').value) || 0,
  };
  try {
    const resp = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await resp.json();
    if (result.valid) renderSimulasiResult(result);
  } catch (err) {
    console.error('Simulate API error:', err);
  }
}

function renderSimulasiResult(result) {
  document.getElementById('cicilanValue').textContent = formatRupiah(result.cicilan);
  document.getElementById('totalBunga').textContent = formatRupiah(result.total_bunga);
  document.getElementById('totalBayar').textContent = formatRupiah(result.total_bayar);
  document.getElementById('bungaEfektif').textContent = formatPct(result.bunga_efektif_tahunan) + ' / tahun';

  const warning = document.getElementById('bungaWarning');
  const warningText = document.getElementById('bungaWarningText');
  const tip = document.getElementById('bungaTip');

  // Reset warning style
  warning.style.background = '';
  warning.style.borderColor = '';
  warning.style.color = '';

  if (result.warning) {
    warning.style.display = 'flex';
    warningText.textContent = result.warning;
  } else {
    warning.style.display = 'none';
  }
  tip.textContent = result.tip || '';
}

// ============================================================
// WAITLIST — Panggil /api/waitlist
// ============================================================
function initWaitlist() {
  const form = document.getElementById('waitlistForm');
  const success = document.getElementById('waitlistSuccess');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('waitlistEmail').value;
    if (!email) return;

    const btn = form.querySelector('button[type=submit]');
    setLoading(btn, true);
    try {
      const resp = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, package: 'general' }),
      });
      await resp.json();
      form.style.display = 'none';
      if (success) success.style.display = 'inline-flex';
    } catch (err) {
      console.error('Waitlist API error:', err);
      alert('Gagal daftar. Coba lagi.');
    } finally {
      setLoading(btn, false);
    }
  });

  // Pricing buttons
  document.querySelectorAll('[data-waitlist]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const emailInput = document.getElementById('waitlistEmail');
      if (emailInput) {
        emailInput.focus();
        emailInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  });
}

// ============================================================
// SMOOTH SCROLL
// ============================================================
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (href === '#' || href === '#!') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const top = target.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
}

// ============================================================
// UI HELPERS
// ============================================================
function setLoading(btn, loading) {
  if (!btn) return;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.textContent = 'Menghitung...';
    btn.disabled = true;
    btn.style.opacity = '0.7';
  } else {
    btn.textContent = btn.dataset.originalText || btn.textContent;
    btn.disabled = false;
    btn.style.opacity = '';
  }
}

function animateCounter(el, target) {
  const start = performance.now();
  const duration = 1000;
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * eased);
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function formatRupiah(n) {
  if (!isFinite(n) || n === 0) return 'Rp 0';
  return 'Rp ' + Math.round(n).toLocaleString('id-ID');
}

function formatPct(n) {
  if (!isFinite(n)) return '0%';
  return n.toFixed(1).replace(/\.0$/, '') + '%';
}

// ============================================================
// CONFETTI (saat skor Aman)
// ============================================================
function triggerConfetti() {
  const colors = ['#b8ff3c', '#9b5de5', '#4ade80', '#facc15', '#ec4899'];
  const container = document.createElement('div');
  container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;';
  document.body.appendChild(container);

  for (let i = 0; i < 50; i++) {
    const conf = document.createElement('div');
    const color = colors[Math.floor(Math.random() * colors.length)];
    const size = 6 + Math.random() * 8;
    const x = Math.random() * window.innerWidth;
    conf.style.cssText = `
      position:absolute;
      top:-20px;left:${x}px;
      width:${size}px;height:${size}px;
      background:${color};
      border-radius:${Math.random() > 0.5 ? '50%' : '2px'};
      animation: confetti-fall ${2 + Math.random() * 2}s linear forwards;
    `;
    container.appendChild(conf);
  }

  setTimeout(() => container.remove(), 4000);
}

// Inject confetti animation
(function() {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes confetti-fall {
      0% { transform: translateY(0) rotate(0deg); opacity: 1; }
      100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
})();
