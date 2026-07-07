// ============================================================
// Galbay Predictor - Produk Page Logic
// 3 Game Changers: Pinjol Checker, Debt Planner, Recovery Roadmap
// Skor Risiko + Simulasi Cicilan (legacy)
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  initPinjolChecker();
  initDebtPlanner();
  initRecoveryRoadmap();
  initSkorForm();
  initSimulasi();
  initWaitlist();
  initSmoothScroll();
  initLockDismiss();
  initRunwayCalculator();
  restoreInitialHashTarget();
});

function getScrollOffset() {
  const topbar = document.querySelector('.topbar');
  return (topbar ? topbar.offsetHeight : 72) + 24;
}

function scrollToElement(target, behavior = 'smooth') {
  if (!target) return;
  const top = target.getBoundingClientRect().top + window.scrollY - getScrollOffset();
  window.scrollTo({ top: Math.max(top, 0), behavior });
}

function restoreInitialHashTarget() {
  if (!window.location.hash || window.location.hash === '#') return;
  const target = document.querySelector(window.location.hash);
  if (!target) return;

  setTimeout(() => {
    scrollToElement(target);
    if (typeof target.focus === 'function') {
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
    }
  }, 80);
}

function getProdukFlags() {
  const el = document.getElementById('produkRuntimeFlags');
  return {
    demoOnly: el?.dataset.demoOnly === '1',
    waitlistEnabled: el?.dataset.waitlistEnabled !== '0',
  };
}
// ============================================================
// 1. PINJOL BLACKLIST CHECKER
// ============================================================
function initPinjolChecker() {
  const form = document.getElementById('pinjolForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('pinjolName').value.trim();
    if (!name) return;

    const btn = form.querySelector('button[type=submit]');
    setLoading(btn, true);

    try {
      const resp = await fetch('/api/check-pinjol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_name: name }),
      });
      const result = await resp.json();
      renderPinjolResult(result);
    } catch (err) {
      console.error('Pinjol API error:', err);
    } finally {
      setLoading(btn, false);
    }
  });
}

function renderPinjolResult(result) {
  const container = document.getElementById('pinjolResult');
  if (!container) return;

  const statusMap = {
    legal: { icon: '✅', color: 'green', label: result.status_label },
    legal_partial: { icon: '🔍', color: 'yellow', label: result.status_label },
    ilegal: { icon: '🚨', color: 'red', label: result.status_label },
    unknown: { icon: '❓', color: 'gray', label: result.status_label },
  };
  const s = statusMap[result.status] || statusMap.unknown;

  container.innerHTML = `
    <div class="pinjol-display">
      <div class="pinjol-status ${s.color}">
        <div class="pinjol-icon">${s.icon}</div>
        <div class="pinjol-name">${result.name}</div>
        <div class="pinjol-label">${s.label}</div>
      </div>
      ${result.ojk_license ? `<div class="pinjol-license">Lisensi OJK: <strong>${result.ojk_license}</strong></div>` : ''}
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin:16px 0;">${result.message}</p>
      ${result.recommendations && result.recommendations.length ? `
        <div class="pinjol-recs">
          <h4>Rekomendasi</h4>
          <ul>
            ${result.recommendations.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      <div class="pinjol-disclaimer">${result.disclaimer || ''}</div>
    </div>
  `;
  setTimeout(() => scrollToElement(container), 120);
}

// ============================================================
// 2. DEBT SNOWBALL / AVALANCHE PLANNER
// ============================================================
function initDebtPlanner() {
  const addBtn = document.getElementById('addDebtBtn');
  const debtsContainer = document.getElementById('plannerDebts');
  const planBtn = document.getElementById('planDebtBtn');
  if (!debtsContainer) return;

  if (addBtn) {
    addBtn.addEventListener('click', () => {
      const row = document.createElement('div');
      row.className = 'debt-row';
      row.innerHTML = `
        <input type="text" class="form-input debt-name" placeholder="Nama utang">
        <div class="rupiah-input"><span class="rupiah-prefix">Rp</span><input type="text" inputmode="numeric" class="form-input rupiah-num debt-balance" placeholder="0"></div>
        <input type="number" class="form-input debt-bunga" placeholder="Bunga %/bln" min="0" step="0.1">
        <div class="rupiah-input"><span class="rupiah-prefix">Rp</span><input type="text" inputmode="numeric" class="form-input rupiah-num debt-min" placeholder="0"></div>
        <button type="button" class="debt-remove" title="Hapus">×</button>
      `;
      debtsContainer.appendChild(row);
      attachRemoveHandler(row);
      attachRupiahFormatter(row);
    });
  }

  document.querySelectorAll('.debt-row').forEach(r => attachRupiahFormatter(r));
  document.querySelectorAll('.rupiah-num').forEach(el => attachRupiahHandler(el));

  document.querySelectorAll('.debt-row').forEach(r => attachRemoveHandler(r));

  if (planBtn) {
    planBtn.addEventListener('click', async () => {
      const debts = collectDebts();
      if (!debts.length) {
        alert('Tambah minimal 1 utang.');
        return;
      }
      const extra = parseRupiahInput(document.getElementById('extraPayment').value);
      setLoading(planBtn, true);
      try {
        const resp = await fetch('/api/debt-planner', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ debts, extra_payment: extra }),
        });
        const result = await resp.json();
        renderDebtPlannerResult(result);
      } catch (err) {
        console.error('Debt planner API error:', err);
      } finally {
        setLoading(planBtn, false);
      }
    });
  }
}

function collectDebts() {
  const rows = document.querySelectorAll('.debt-row');
  const debts = [];
  rows.forEach(r => {
    const name = r.querySelector('.debt-name').value.trim();
    const balance = parseRupiahInput(r.querySelector('.debt-balance').value);
    const bunga = parseFloat(r.querySelector('.debt-bunga').value) || 0;
    const min = parseRupiahInput(r.querySelector('.debt-min').value);
    if (name && balance > 0) {
      debts.push({ name, balance, bunga_pct: bunga, min_payment: min });
    }
  });
  return debts;
}

function attachRemoveHandler(row) {
  const btn = row.querySelector('.debt-remove');
  if (btn) {
    btn.addEventListener('click', () => {
      if (document.querySelectorAll('.debt-row').length > 1) {
        row.remove();
      } else {
        alert('Minimal 1 utang.');
      }
    });
  }
}

function renderDebtPlannerResult(result) {
  const container = document.getElementById('plannerResult');
  if (!container) return;
  if (!result.valid) {
    container.innerHTML = `<div class="skor-placeholder"><p>${result.error || 'Error'}</p></div>`;
    setTimeout(() => scrollToElement(container), 120);
    return;
  }

  const { snowball, avalanche, recommendation, reason, total_debt } = result;
  const recStrategy = recommendation === 'snowball' ? snowball : avalanche;
  const altStrategy = recommendation === 'snowball' ? avalanche : snowball;
  const interestSaved = altStrategy.total_interest_paid - recStrategy.total_interest_paid;

  container.innerHTML = `
    <div class="planner-display">
      <div class="planner-summary">
        <div class="planner-stat">
          <div class="planner-stat-label">Total Utang</div>
          <div class="planner-stat-value">${formatRupiah(total_debt)}</div>
        </div>
        <div class="planner-stat">
          <div class="planner-stat-label">Rekomendasi</div>
          <div class="planner-stat-value highlight">${recStrategy.strategy_label.split(' (')[0]}</div>
          <div class="planner-stat-sub">${reason}</div>
        </div>
      </div>

      <div class="planner-strategy recommended">
        <h4>✅ ${recStrategy.strategy_label}</h4>
        <div class="planner-strategy-stats">
          <div><strong>${recStrategy.months_to_debt_free}</strong> bulan</div>
          <div>Bunga total: <strong>${formatRupiah(recStrategy.total_interest_paid)}</strong></div>
        </div>
        <div class="planner-order">
          <strong>Urutan bayar:</strong>
          ${recStrategy.order.map((name, i) => `<span class="order-pill">${i+1}. ${name}</span>`).join(' ')}
        </div>
        <div class="planner-schedule">
          <strong>Estimasi lunas:</strong>
          ${Object.entries(recStrategy.paid_off_schedule).map(([name, m]) =>
            m ? `${name}: <strong>bulan ${m}</strong>` : `${name}: -`
          ).join(' &middot; ')}
        </div>
      </div>

      <div class="planner-strategy alt">
        <h4>Alternatif: ${altStrategy.strategy_label}</h4>
        <div class="planner-strategy-stats">
          <div><strong>${altStrategy.months_to_debt_free}</strong> bulan</div>
          <div>Bunga total: <strong>${formatRupiah(altStrategy.total_interest_paid)}</strong></div>
          ${interestSaved > 0 ? `<div class="planner-saved">Hemat ${formatRupiah(interestSaved)} dengan rekomendasi</div>` : ''}
        </div>
      </div>

      <div class="planner-disclaimer">${result.disclaimer || ''}</div>
    </div>
  `;
  setTimeout(() => scrollToElement(container), 120);
}

// ============================================================
// 3. RECOVERY ROADMAP
// ============================================================
function initRecoveryRoadmap() {
  const form = document.getElementById('roadmapForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type=submit]');
    setLoading(btn, true);

    const payload = {
      total_utang: parseRupiahInput(document.getElementById('rmTotalUtang').value),
      income_bulanan: parseRupiahInput(document.getElementById('rmIncome').value),
      sudah_dc: document.querySelector('input[name=rmSudahDc]:checked')?.value === '1',
      hari_telat: parseInt(document.getElementById('rmHariTelat').value) || 0,
    };

    try {
      const resp = await fetch('/api/recovery-roadmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await resp.json();
      renderRoadmapResult(result);
    } catch (err) {
      console.error('Roadmap API error:', err);
    } finally {
      setLoading(btn, false);
    }
  });
}

function renderRoadmapResult(result) {
  const container = document.getElementById('roadmapResult');
  if (!container) return;
  if (!result.valid) {
    container.innerHTML = `<div class="skor-placeholder"><p>${result.error || 'Error'}</p></div>`;
    setTimeout(() => scrollToElement(container), 120);
    return;
  }

  const sevColor = { kritis: 'red', tinggi: 'orange', sedang: 'green' }[result.severity] || 'gray';

  container.innerHTML = `
    <div class="roadmap-display">
      <div class="roadmap-severity ${sevColor}">
        <div class="roadmap-severity-label">Severity</div>
        <div class="roadmap-severity-value">${result.severity_label}</div>
        <div class="roadmap-ratio">Debt-to-income ratio: ${result.conditions.debt_to_income_ratio}x</div>
      </div>

      <div class="roadmap-phase">
        <div class="roadmap-phase-header"><span class="phase-badge">MINGGU 1-2</span><span class="phase-label">Audit &amp; Stabilisasi</span></div>
        <ul class="roadmap-list">${result.roadmap.minggu_1_2.map(item => `<li>${item}</li>`).join('')}</ul>
      </div>

      <div class="roadmap-phase">
        <div class="roadmap-phase-header"><span class="phase-badge">MINGGU 3-4</span><span class="phase-label">Eksekusi &amp; Negosiasi</span></div>
        <ul class="roadmap-list">${result.roadmap.minggu_3_4.map(item => `<li>${item}</li>`).join('')}</ul>
      </div>

      <div class="roadmap-phase">
        <div class="roadmap-phase-header"><span class="phase-badge">BULAN 3</span><span class="phase-label">Recovery &amp; Momentum</span></div>
        <ul class="roadmap-list">${result.roadmap.bulan_3.map(item => `<li>${item}</li>`).join('')}</ul>
      </div>

      <div class="roadmap-metrics">
        <h4>Target Sukses</h4>
        <div class="roadmap-metric"><span>Bulan 1:</span> ${result.success_metrics.target_bulan_1}</div>
        <div class="roadmap-metric"><span>Bulan 2:</span> ${result.success_metrics.target_bulan_2}</div>
        <div class="roadmap-metric"><span>Bulan 3:</span> ${result.success_metrics.target_bulan_3}</div>
      </div>

      <div class="roadmap-disclaimer">${result.disclaimer}</div>
    </div>
  `;
  setTimeout(() => scrollToElement(container), 120);
}

// ============================================================
// SKOR RISIKO GALBAY (legacy)
// ============================================================
function initSkorForm() {
  const form = document.getElementById('skorForm');
  if (!form) return;

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
        apps, utang: fd.get('utang') || '0',
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
      <div class="skor-circle skor-${category}" style="--p: ${score}%;">
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
        ${recommendations.map((rec, i) => `<div class="skor-rec-item"><div class="skor-rec-num">${i + 1}</div><div>${rec}</div></div>`).join('')}
      </div>
      <div class="skor-version">Model: ${model_version}</div>
    </div>`;
  const numEl = container.querySelector('.skor-number');
  if (numEl) animateCounter(numEl, parseInt(numEl.dataset.target, 10));
  if (category === 'aman') setTimeout(() => triggerConfetti(), 300);
  setTimeout(() => scrollToElement(container), 120);
}

function renderSkorError() {
  const c = document.getElementById('skorResult');
  if (c) c.innerHTML = `<div class="skor-placeholder"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><p>Terjadi kesalahan. Coba lagi.</p></div>`;
  if (c) setTimeout(() => scrollToElement(c), 120);
}

// ============================================================
// SIMULASI CICILAN (legacy)
// ============================================================
function initSimulasi() {
  const nominal = document.getElementById('nominal');
  const bunga = document.getElementById('bunga');
  const tenor = document.getElementById('tenor');
  const admin = document.getElementById('admin');
  if (!nominal) return;
  const bungaValue = document.getElementById('bungaValue');
  if (bungaValue) bunga.addEventListener('input', () => { bungaValue.textContent = bunga.value; });
  let debounce;
  [nominal, bunga, tenor, admin].forEach(el => {
    el.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(updateSimulasi, 200); });
    el.addEventListener('change', updateSimulasi);
  });
  updateSimulasi();
}

async function updateSimulasi() {
  try {
    const resp = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nominal: parseRupiahInput(document.getElementById('nominal').value),
        bunga_pct: parseFloat(document.getElementById('bunga').value) || 0,
        tenor: parseInt(document.getElementById('tenor').value) || 1,
        admin: parseRupiahInput(document.getElementById('admin').value),
      }),
    });
    const result = await resp.json();
    if (result.valid) renderSimulasiResult(result);
  } catch (err) { console.error(err); }
}

function renderSimulasiResult(result) {
  document.getElementById('cicilanValue').textContent = formatRupiah(result.cicilan);
  document.getElementById('totalBunga').textContent = formatRupiah(result.total_bunga);
  document.getElementById('totalBayar').textContent = formatRupiah(result.total_bayar);
  document.getElementById('bungaEfektif').textContent = formatPct(result.bunga_efektif_tahunan) + ' / tahun';
  const warning = document.getElementById('bungaWarning');
  const warningText = document.getElementById('bungaWarningText');
  const tip = document.getElementById('bungaTip');
  warning.style.background = ''; warning.style.borderColor = ''; warning.style.color = '';
  if (result.warning) {
    warning.style.display = 'flex';
    warningText.textContent = result.warning;
  } else {
    warning.style.display = 'none';
  }
  tip.textContent = result.tip || '';
}

// ============================================================
// WAITLIST (legacy) + PREMIUM MODAL
// ============================================================
function initWaitlist() {
  const flags = getProdukFlags();
  const form = document.getElementById('waitlistForm');
  const success = document.getElementById('waitlistSuccess');
  if (form) {
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
        const result = await resp.json();
        form.style.display = 'none';
        if (success) {
          const successText = success.querySelector('span');
          if (successText && result?.message) successText.textContent = result.message;
          success.style.display = 'inline-flex';
        }
      } catch (err) { console.error(err); alert('Gagal daftar. Coba lagi.'); }
      finally { setLoading(btn, false); }
    });
  }
  document.querySelectorAll('[data-waitlist]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const pkg = btn.getAttribute('data-waitlist');
      if (pkg === 'premium') {
        showPremiumModal();
      } else {
        if (!flags.waitlistEnabled && success) {
          const successText = success.querySelector('span');
          if (successText) {
            successText.textContent = flags.demoOnly
              ? 'Public demo aktif. Fitur ini hanya ditampilkan sebagai preview dan tidak menyimpan permintaan baru.'
              : 'Flow ini tidak menyimpan data baru pada mode saat ini.';
          }
          success.style.display = 'inline-flex';
          scrollToElement(success);
          return;
        }
        const emailInput = document.getElementById('waitlistEmail');
        if (emailInput) {
          emailInput.focus();
          scrollToElement(emailInput);
        }
      }
    });
  });

  // Premium modal wiring
  initPremiumModal();
}

// ============================================================
// PREMIUM MODAL
// ============================================================
function showPremiumModal() {
  const modal = document.getElementById('premiumModal');
  if (!modal) return;
  // Spawn particles (idempotent)
  const particlesEl = document.getElementById('premiumParticles');
  if (particlesEl && !particlesEl.dataset.spawned) {
    particlesEl.dataset.spawned = '1';
    for (let i = 0; i < 30; i++) {
      const p = document.createElement('div');
      p.className = 'premium-particle';
      p.style.left = Math.random() * 100 + '%';
      p.style.top = (50 + Math.random() * 50) + '%';
      p.style.animationDelay = (Math.random() * 8) + 's';
      p.style.animationDuration = (6 + Math.random() * 4) + 's';
      p.style.width = p.style.height = (4 + Math.random() * 5) + 'px';
      particlesEl.appendChild(p);
    }
  }
  resetPremiumModal();
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  setTimeout(() => {
    const nameInput = document.getElementById('premiumName');
    if (nameInput) nameInput.focus();
  }, 300);
}

function closePremiumModal() {
  const modal = document.getElementById('premiumModal');
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';

  const content = document.getElementById('premiumContent');
  if (content?.dataset.state === 'success') {
    window.setTimeout(() => resetPremiumModal(), 180);
  }
}

function initPremiumModal() {
  const modal = document.getElementById('premiumModal');
  if (!modal) return;
  const content = document.getElementById('premiumContent');
  if (content && !content.dataset.initialMarkup) {
    content.dataset.initialMarkup = content.innerHTML;
    content.dataset.state = 'form';
  }
  const closeBtn = document.getElementById('premiumCloseBtn');
  if (closeBtn) closeBtn.addEventListener('click', closePremiumModal);

  // Backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closePremiumModal();
  });

  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('open')) closePremiumModal();
  });

  bindPremiumForm();
}

function bindPremiumForm() {
  const flags = getProdukFlags();
  const form = document.getElementById('premiumForm');
  if (!form || form.dataset.bound === '1') return;

  form.dataset.bound = '1';
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('premiumName').value.trim();
    const email = document.getElementById('premiumEmail').value.trim();
    if (!name || !email) return;
    const submitBtn = form.querySelector('.premium-submit');
    setLoading(submitBtn, true);
    try {
      const resp = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, package: 'premium' }),
      });
      const result = await resp.json();
      showPremiumSuccess(name, result?.message, flags.demoOnly);
    } catch (err) {
      console.error('Premium submit error:', err);
      alert('Gagal aktivasi. Coba lagi.');
      setLoading(submitBtn, false);
    }
  });
}

function resetPremiumModal() {
  const content = document.getElementById('premiumContent');
  if (!content?.dataset.initialMarkup) return;
  if (content.dataset.state !== 'success') return;

  content.innerHTML = content.dataset.initialMarkup;
  content.dataset.state = 'form';
  bindPremiumForm();
}

function showPremiumSuccess(name, message, demoOnly = false) {
  const content = document.getElementById('premiumContent');
  if (!content) return;
  content.dataset.state = 'success';
  content.innerHTML = `
    <div class="premium-success">
      <div class="premium-success-icon">✓</div>
      <h3>${demoOnly ? `Preview siap, ${escapeHtml(name)}!` : `Selamat, ${escapeHtml(name)}!`}</h3>
      <p>${escapeHtml(message || (demoOnly
        ? 'Mode public demo aktif. Form ini tidak menyimpan aktivasi permanen, tetapi paket premium sudah siap kamu jelaskan saat demo.'
        : 'Kamu sudah masuk daftar Premium. Cek email kamu dalam 24 jam untuk link aktivasi.'
      ))}</p>
      <button type="button" class="premium-submit" id="premiumDoneBtn" style="margin-top:20px;">🎉 Tutup</button>
    </div>
  `;
  const doneBtn = document.getElementById('premiumDoneBtn');
  if (doneBtn) doneBtn.addEventListener('click', closePremiumModal);
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// ============================================================
// 5. EMERGENCY RUNWAY CALCULATOR (NEW in Round 10)
// ============================================================
function initRunwayCalculator() {
  const form = document.getElementById('runwayForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cash = parseRupiah(document.getElementById('rwCash').value);
    const expenses = parseRupiah(document.getElementById('rwExpenses').value);
    const income = parseRupiah(document.getElementById('rwIncome').value);
    const debt = parseRupiah(document.getElementById('rwDebt').value);

    if (expenses <= 0) {
      alert('Pengeluaran bulanan harus > 0');
      return;
    }

    try {
      const r = await fetch('/tools/emergency-runway', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cash, expenses, income, debt_payment: debt }),
      });
      const result = await r.json();
      renderRunwayResult(result);
    } catch (err) {
      console.error('Runway calc error:', err);
      alert('Gagal hitung. Coba lagi.');
    }
  });
}

function renderRunwayResult(result) {
  const card = document.getElementById('runwayResult');
  if (!result.valid) {
    card.innerHTML = '<p style="color:#ef4444;">' + (result.error || 'Error') + '</p>';
    card.style.display = 'block';
    return;
  }
  const fmtIDR = (n) => n.toLocaleString('id-ID');
  let recsHtml = '';
  if (result.recommendations && result.recommendations.length) {
    recsHtml = '<div class="runway-recs">';
    result.recommendations.forEach((r) => {
      recsHtml += `
        <div class="runway-rec">
          <span class="runway-rec-priority priority-${r.priority}">${r.priority}</span>
          <div class="runway-rec-content">
            <div class="runway-rec-title">${r.title}</div>
            <div class="runway-rec-action">${r.action}</div>
          </div>
        </div>`;
    });
    recsHtml += '</div>';
  }
  card.style.setProperty('--status-color', result.status_color);
  card.innerHTML = `
    <div class="runway-num">${result.runway_months}</div>
    <div class="runway-label">${result.runway_label} runway</div>
    <div class="runway-status">${result.status}</div>
    <p class="runway-msg">${result.status_msg}</p>
    <div style="display:flex; gap:20px; justify-content:center; margin-bottom:24px; flex-wrap:wrap;">
      <div style="text-align:center;">
        <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em;">Total Burn/Bulan</div>
        <div style="font-size:1.4rem; font-weight:800; color:var(--accent-violet);">Rp ${fmtIDR(result.total_burn)}</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em;">Income Coverage</div>
        <div style="font-size:1.4rem; font-weight:800; color:${result.income_coverage >= 100 ? '#84cc16' : '#f59e0b'};">${result.income_coverage}%</div>
      </div>
    </div>
    ${recsHtml}
    <div style="margin-top:24px; text-align:center;">
      <a href="/galbay-score" class="btn-secondary">⚡ Cek Galbay Score Lengkap</a>
    </div>
  `;
  card.style.display = 'block';
  // Smooth scroll to result
  setTimeout(() => scrollToElement(card), 100);
}

function parseRupiah(str) {
  if (!str) return 0;
  return parseInt(String(str).replace(/[^\d]/g, ''), 10) || 0;
}

// ============================================================
// 5. SMOOTH SCROLL
// ============================================================
function initSmoothScroll() {
  document.querySelectorAll('a[href*="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (!href || href === '#' || href === '#!') return;

      const parsed = new URL(href, window.location.href);
      if (!parsed.hash || parsed.pathname !== window.location.pathname) return;

      const target = document.querySelector(parsed.hash);
      if (!target) return;

      e.preventDefault();
      history.replaceState(null, '', `${window.location.pathname}${window.location.search}${parsed.hash}`);
      scrollToElement(target);
    });
  });
}

// ============================================================
// LOCK OVERLAY DISMISS (close button + free feature link)
// ============================================================
function initLockDismiss() {
  document.querySelectorAll('[data-lock-dismiss]').forEach(el => {
    el.addEventListener('click', (e) => {
      const sectionId = el.dataset.lockDismiss;
      const section = document.getElementById(sectionId);
      if (!section) return;
      // For close button: prevent default & dismiss
      if (el.classList.contains('lock-close')) {
        e.preventDefault();
        section.classList.add('is-dismissed');
      }
      // For free link: dismiss + scroll (default anchor scroll will happen)
      if (el.classList.contains('lock-free-link')) {
        e.preventDefault();
        section.classList.add('is-dismissed');
        const targetHref = el.getAttribute('href');
        const target = document.querySelector(targetHref);
        if (target) {
          scrollToElement(target);
        }
      }
    });
  });
  // Re-show on hash change if user navigates back
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    const href = link.getAttribute('href');
    if (href && href.startsWith('#')) {
      const targetId = href.substring(1);
      // Re-show all dismissed locks
      document.querySelectorAll('.feature-locked.is-dismissed').forEach(s => {
        s.classList.remove('is-dismissed');
      });
    }
  });
}

function setLoading(btn, loading) {
  if (!btn) return;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.textContent = 'Memproses...';
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

function triggerConfetti() {
  const colors = ['#84cc16', '#6366f1', '#16a34a', '#2563eb', '#ec4899'];
  const container = document.createElement('div');
  container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;';
  document.body.appendChild(container);
  for (let i = 0; i < 50; i++) {
    const conf = document.createElement('div');
    const color = colors[Math.floor(Math.random() * colors.length)];
    const size = 6 + Math.random() * 8;
    const x = Math.random() * window.innerWidth;
    conf.style.cssText = `position:absolute;top:-20px;left:${x}px;width:${size}px;height:${size}px;background:${color};border-radius:${Math.random() > 0.5 ? '50%' : '2px'};animation: confetti-fall ${2 + Math.random() * 2}s linear forwards;`;
    container.appendChild(conf);
  }
  setTimeout(() => container.remove(), 4000);
}

(function() {
  const style = document.createElement('style');
  style.textContent = `@keyframes confetti-fall { 0% { transform: translateY(0) rotate(0deg); opacity: 1; } 100% { transform: translateY(100vh) rotate(720deg); opacity: 0; } }`;
  document.head.appendChild(style);
})();

// ============================================================
// RUPIAH FORMATTER — Input dengan separator 5.000.000
// ============================================================
function formatRupiahLive(str) {
  const digits = String(str || '').replace(/[^\d]/g, '');
  if (!digits) return '';
  return parseInt(digits, 10).toLocaleString('id-ID');
}

function parseRupiahInput(str) {
  const digits = String(str || '').replace(/[^\d]/g, '');
  return digits ? parseInt(digits, 10) : 0;
}

function attachRupiahHandler(el) {
  if (!el || el.dataset.rupiahBound) return;
  el.dataset.rupiahBound = '1';
  el.addEventListener('input', (e) => {
    const cursor = el.selectionStart;
    const before = el.value.length;
    el.value = formatRupiahLive(el.value);
    const after = el.value.length;
    const newPos = cursor + (after - before);
    try { el.setSelectionRange(newPos, newPos); } catch (e) {}
  });
  el.addEventListener('blur', () => {
    if (el.value && !el.value.startsWith('Rp')) {
      const n = parseRupiahInput(el.value);
      el.value = n ? n.toLocaleString('id-ID') : '';
    }
  });
}

function attachRupiahFormatter(root) {
  root.querySelectorAll('.rupiah-num').forEach(el => attachRupiahHandler(el));
}

// Auto-bind semua .rupiah-num di DOM siap
(function() {
  function bindAll() {
    document.querySelectorAll('.rupiah-num').forEach(el => attachRupiahHandler(el));
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindAll);
  } else {
    bindAll();
  }
})();
