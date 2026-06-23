// ============================================================
// Galbay Predictor - Produk Page Logic
// Skor Risiko Galbay (rule-based) + Simulasi Cicilan + Waitlist
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  initSkorForm();
  initSimulasi();
  initWaitlist();
});

// ============================================================
// SKOR RISIKO GALBAY — Rule-based scoring
// ============================================================
function initSkorForm() {
  const form = document.getElementById('skorForm');
  if (!form) return;

  // Slider live update
  const slider = document.getElementById('selfrewardSlider');
  const sliderValue = document.getElementById('selfrewardValue');
  if (slider && sliderValue) {
    slider.addEventListener('input', () => {
      sliderValue.textContent = slider.value;
    });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const inputs = collectFormInputs(form);
    const result = calculateSkor(inputs);
    renderSkorResult(result);
  });
}

function collectFormInputs(form) {
  const fd = new FormData(form);
  const apps = fd.getAll('apps');
  const utang = fd.get('utang') || '0';
  const selfreward = parseInt(fd.get('selfreward') || '3', 10);
  const telat = fd.get('telat') || '0';
  const dc = fd.get('dc') || '0';
  const feeling = fd.get('feeling') || '0';
  return { apps, utang, selfreward, telat, dc, feeling };
}

function calculateSkor({ apps, utang, selfreward, telat, dc, feeling }) {
  // Bobot risiko per faktor (total max ~135, kita cap ke 100)
  let risk = 0;
  const factors = [];

  // 1. Apps (max +38)
  const appRisk = { pinjol: 20, paylater: 10, ewallet: 5, bank: 3 };
  apps.forEach(app => {
    const r = appRisk[app] || 0;
    risk += r;
    if (r > 0) factors.push({ name: app, weight: r, type: 'apps' });
  });

  // 2. Utang (0 / 10 / 20 / 30)
  const utangRisk = { '0': 0, lt5: 10, '5to20': 20, gt20: 30 };
  const ur = utangRisk[utang] || 0;
  risk += ur;
  if (ur > 0) factors.push({ name: 'utang', weight: ur, type: 'utang' });

  // 3. Self reward (max +25)
  let sr = 5;
  if (selfreward > 3 && selfreward <= 6) sr = 15;
  else if (selfreward > 6) sr = 25;
  risk += sr;
  if (sr > 5) factors.push({ name: 'self_reward', weight: sr, type: 'selfreward' });

  // 4. Telat bayar (0 / 15 / 25)
  const tr = { '0': 0, '1': 15, '2': 25 }[telat] || 0;
  risk += tr;
  if (tr > 0) factors.push({ name: 'telat', weight: tr, type: 'telat' });

  // 5. DC (0 / 25)
  const dcr = { '0': 0, '1': 25 }[dc] || 0;
  risk += dcr;
  if (dcr > 0) factors.push({ name: 'dc', weight: dcr, type: 'dc' });

  // 6. Feeling (0 / 10 / 15)
  const fr = { '0': 0, '1': 10, '2': 15 }[feeling] || 0;
  risk += fr;
  if (fr > 0) factors.push({ name: 'feeling', weight: fr, type: 'feeling' });

  // Cap 0-100
  const score = Math.min(100, Math.round(risk));
  const category = score <= 30 ? 'aman' : (score <= 60 ? 'waspada' : 'bahaya');

  return { score, category, factors, inputs: { apps, utang, selfreward, telat, dc, feeling } };
}

function renderSkorResult({ score, category, factors, inputs }) {
  const container = document.getElementById('skorResult');
  if (!container) return;

  const labels = {
    aman: { name: 'AMAN', desc: 'Keuangan digital kamu sehat. Pertahankan pola ini!' },
    waspada: { name: 'WASPADA', desc: 'Ada tanda-tanda risiko. Mulai hati-hati dan evaluasi kebiasaan.' },
    bahaya: { name: 'BAHAYA', desc: 'Risiko galbay tinggi. Butuh intervensi dan perubahan perilaku segera.' },
  };
  const cat = labels[category];

  // Top 3 recommendations by weight
  const top3 = factors
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 3)
    .map(f => getRecommendation(f.type));

  container.innerHTML = `
    <div class="skor-display">
      <div class="skor-circle" style="--p: ${score}%;">
        <div class="skor-number">${score}</div>
        <div class="skor-label">/ 100</div>
      </div>
      <div class="skor-category ${category}">${cat.name}</div>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:24px;">${cat.desc}</p>
      <div class="skor-recs">
        <h4>3 Rekomendasi Utama</h4>
        ${top3.map((rec, i) => `
          <div class="skor-rec-item">
            <div class="skor-rec-num">${i + 1}</div>
            <div>${rec}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function getRecommendation(type) {
  const recs = {
    apps: '<strong>Hindari pinjol baru.</strong> Prioritaskan melunasi yang ada. Cek modul <em>Cara Recovery dari Galbay</em>.',
    utang: '<strong>Buat rencana pembayaran.</strong> Prioritaskan utang dengan bunga tertinggi (avalanche method).',
    selfreward: '<strong>Tunda checkout 24 jam.</strong> Gunakan aturan "tidur dulu sebelum bayar". Coba Simulasi Cicilan sebelum deal.',
    telat: '<strong>Setel auto-debit.</strong> Aktifkan pengingat tagihan H-3. Keterlambatan = biaya tambahan yang memberatkan.',
    dc: '<strong>Jangan hindari, negosiasikan.</strong> Lihat modul <em>Cara Negosiasi dengan DC</em>. Kamu punya hak sebagai borrower.',
    feeling: '<strong>Jangan abaikan sinyal.</strong> Stress finansial itu nyata. Pertimbangkan sesi konseling atau modul <em>Habit Building</em>.',
  };
  return recs[type] || 'Pertahankan perilaku baik dan terus monitor keuangan.';
}

// ============================================================
// SIMULASI CICILAN — Real-time calculator
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

  [nominal, bunga, tenor, admin].forEach(el => {
    el.addEventListener('input', updateSimulasi);
    el.addEventListener('change', updateSimulasi);
  });
  updateSimulasi();
}

function updateSimulasi() {
  const nominal = parseFloat(document.getElementById('nominal').value) || 0;
  const bungaPct = parseFloat(document.getElementById('bunga').value) || 0;
  const tenor = parseInt(document.getElementById('tenor').value) || 1;
  const admin = parseFloat(document.getElementById('admin').value) || 0;

  // Total bunga = nominal × (bunga/100) × tenor
  const totalBunga = nominal * (bungaPct / 100) * tenor;
  const totalBayar = nominal + totalBunga + admin;
  const cicilan = totalBayar / tenor;
  // Bunga efektif tahunan = (total bunga / nominal) × (12 / tenor) × 100
  const bungaEfektif = (totalBunga / nominal) * (12 / tenor) * 100;

  document.getElementById('cicilanValue').textContent = formatRupiah(cicilan);
  document.getElementById('totalBunga').textContent = formatRupiah(totalBunga);
  document.getElementById('totalBayar').textContent = formatRupiah(totalBayar);
  document.getElementById('bungaEfektif').textContent = formatPct(bungaEfektif) + ' / tahun';

  // Warning + tip
  const warning = document.getElementById('bungaWarning');
  const warningText = document.getElementById('bungaWarningText');
  const tip = document.getElementById('bungaTip');

  if (bungaEfektif > 100) {
    warning.style.display = 'flex';
    warningText.textContent = `Bunga efektif ${formatPct(bungaEfektif)}/tahun — ${(bungaEfektif / 12).toFixed(0)}x lipat KTA bank (~12%). Sangat memberatkan. Pertimbangkan opsi lain.`;
    tip.innerHTML = '<strong>Tips:</strong> Bunga >100%/tahun = predatory lending. Coba negosiasi tenor lebih panjang atau cari alternatif KTA bank.';
  } else if (bungaEfektif > 36) {
    warning.style.display = 'flex';
    warning.style.background = 'rgba(250,204,21,0.1)';
    warning.style.borderColor = 'rgba(250,204,21,0.3)';
    warning.style.color = '#facc15';
    warningText.textContent = `Bunga efektif ${formatPct(bungaEfektif)}/tahun — di atas rata-rata KTA bank (12-18%). Hati-hati.`;
    tip.innerHTML = '<strong>Tips:</strong> Masih dalam batas wajar tapi bisa dinegosiasi. Bandingkan dengan KTA bank sebelum commit.';
  } else if (bungaEfektif > 18) {
    warning.style.display = 'none';
    tip.innerHTML = '<strong>Tips:</strong> Bunga dalam batas wajar. Pastikan tenor sesuai kemampuan bayar bulanan.';
  } else {
    warning.style.display = 'none';
    tip.innerHTML = '<strong>Tips:</strong> Bunga rendah. Pastikan tidak ada biaya tersembunyi lain (asuransi, provisi).';
  }
}

// ============================================================
// WAITLIST — Form handler
// ============================================================
function initWaitlist() {
  const form = document.getElementById('waitlistForm');
  const success = document.getElementById('waitlistSuccess');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('waitlistEmail').value;
    if (!email) return;

    // Log ke console untuk demo
    console.log('Waitlist signup:', email);
    // Simpan ke localStorage
    try {
      const list = JSON.parse(localStorage.getItem('galbay_waitlist') || '[]');
      list.push({ email, timestamp: new Date().toISOString() });
      localStorage.setItem('galbay_waitlist', JSON.stringify(list));
    } catch (e) { /* noop */ }

    form.style.display = 'none';
    if (success) success.style.display = 'inline-flex';
  });

  // Pricing buttons → juga trigger waitlist
  document.querySelectorAll('[data-waitlist]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const pkg = btn.dataset.waitlist;
      const emailInput = document.getElementById('waitlistEmail');
      if (emailInput) {
        emailInput.focus();
        emailInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      console.log('Pricing CTA clicked:', pkg);
    });
  });
}

// ============================================================
// HELPERS
// ============================================================
function formatRupiah(n) {
  if (!isFinite(n) || n === 0) return 'Rp 0';
  return 'Rp ' + Math.round(n).toLocaleString('id-ID');
}
function formatPct(n) {
  if (!isFinite(n)) return '0%';
  return n.toFixed(1).replace(/\.0$/, '') + '%';
}
