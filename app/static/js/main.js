// ============================================================
// Galbay Predictor - Dashboard logic (data asli 349K + VADER)
// Data di-load dari data.js (window.GALBAY_DATA)
// Conditional chart init: hanya render chart yang canvas-nya ada di page
// ============================================================
const D = window.GALBAY_DATA || {};
const COL = { lime:'#b8ff3c', pur:'#9b5de5', violet:'#6a0dad', red:'#f87171', org:'#f97316', blu:'#3b82f6', grn:'#4ade80', gray:'#6b5e80', text:'#a89ac0' };

document.addEventListener('DOMContentLoaded', () => {
  fillNumbers();
  if (window.Chart) initCharts();
  renderTopAppsTable();
  initAnimations();
  initCounters();
  initScrollTop();
  initHamburger();
  initDropdown();
});

// ── Isi angka teks dari data (elemen ber-atribut data-fill) ──
function fillNumbers() {
  const m = D.meta || {}, mo = D.model || {};
  const map = {
    total_reviews: (m.total_reviews||0).toLocaleString('id-ID'),
    total_relevant: (m.total_relevant||0).toLocaleString('id-ID'),
    n_apps: m.n_apps, n_categories: m.n_categories,
    n_news: m.n_news, n_forum: m.n_forum,
    date_min: m.date_min, date_max: m.date_max,
    distress_total: (m.distress_total||0).toLocaleString('id-ID'),
    distress_pct: m.distress_pct + '%',
    acc: (mo.accuracy*100).toFixed(1) + '%',
    prec: (mo.precision*100).toFixed(1) + '%',
    rec: (mo.recall*100).toFixed(1) + '%',
    f1: (mo.f1*100).toFixed(1) + '%',
    vocab: (mo.vocab||0).toLocaleString('id-ID'),
    n_train: (mo.n_train||0).toLocaleString('id-ID'),
    n_test: (mo.n_test||0).toLocaleString('id-ID'),
  };
  document.querySelectorAll('[data-fill]').forEach(el => {
    const k = el.dataset.fill;
    if (map[k] !== undefined && map[k] !== null) el.textContent = map[k];
  });
}

// ── COUNTER ANIMATION ──
function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.dataset.done) {
        entry.target.dataset.done = '1';
        animateCounter(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(c => observer.observe(c));
}
function animateCounter(el) {
  const target = parseFloat(el.dataset.count);
  const suffix = el.dataset.suffix || '';
  const prefix = el.dataset.prefix || '';
  const start = performance.now(), duration = 1600;
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    const cur = target * eased;
    const disp = target < 100 && !Number.isInteger(target) ? cur.toFixed(1) : Math.round(cur).toLocaleString('id-ID');
    el.textContent = prefix + disp + suffix;
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── FADE ANIMATIONS ──
function initAnimations() {
  const els = document.querySelectorAll('.chart-card, .info-card, .kpi-card, .bmc-block, .metric-card, .insight-box, .top-apps-table');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => { entry.target.style.opacity = '1'; entry.target.style.transform = 'translateY(0)'; }, i * 40);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  els.forEach(el => {
    el.style.opacity = '0'; el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
  });
}

// ── SCROLL-TO-TOP BUTTON ──
function initScrollTop() {
  const btn = document.getElementById('scrollTop');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ── MOBILE HAMBURGER ──
function initHamburger() {
  const btn = document.getElementById('hamburger');
  const nav = document.getElementById('topbarNav');
  if (!btn || !nav) return;
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    btn.innerHTML = isOpen ? '&times;' : '&#9776;';
  });
  document.addEventListener('click', (e) => {
    if (!nav.contains(e.target) && !btn.contains(e.target) && nav.classList.contains('open')) {
      nav.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '&#9776;';
    }
  });
  nav.querySelectorAll('.nav-pill').forEach(p => {
    p.addEventListener('click', () => {
      nav.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '&#9776;';
    });
  });
}

// ── DROPDOWN (More menu) ──
function initDropdown() {
  const toggle = document.getElementById('moreBtn');
  const menu = document.getElementById('moreMenu');
  if (!toggle || !menu) return;
  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target) && !toggle.contains(e.target) && menu.classList.contains('open')) {
      menu.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}

// ── CHART DEFAULTS ──
const chartDefaults = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: COL.text, font: { family: 'Inter', size: 12 }, boxWidth: 12 } },
    tooltip: { backgroundColor: '#120038', borderColor: 'rgba(155,93,229,0.4)', borderWidth: 1, titleColor: '#f0eaff', bodyColor: COL.text, padding: 12 }
  }
};
const grid = { ticks: { color: COL.gray }, grid: { color: 'rgba(155,93,229,0.1)' } };
const gridY = { ticks: { color: COL.text, font:{size:11} }, grid: { display:false } };
function make(id, cfg){ const el=document.getElementById(id); if(!el) return; new Chart(el, cfg); }

// ── CONDITIONAL CHART INIT: hanya render chart yang canvas ada di page ──
function initCharts() {
  Chart.defaults.color = COL.text;
  const ids = new Set();
  document.querySelectorAll('canvas[id]').forEach(c => ids.add(c.id));

  if (ids.has('chartScoreDist')) chartScoreDist();
  if (ids.has('chartScoreDist2')) chartScoreDist2();
  if (ids.has('chartCategory')) chartCategory();
  if (ids.has('chartTimeline')) chartTimeline();
  if (ids.has('chartBehavior')) chartBehavior();
  if (ids.has('chartKeywords')) chartKeywords();
  if (ids.has('chartWordcloud')) chartWordcloud();
  if (ids.has('chartSentimentCat')) chartSentimentCat();
  if (ids.has('chartTopApps')) chartTopApps();
  if (ids.has('chartSentimentDist')) chartSentimentDist();
  if (ids.has('chartModel')) chartModel();
}

// 1) Distribusi skor rating
function chartScoreDist() {
  const s = D.score_dist || {};
  make('chartScoreDist', { type:'bar', data:{
    labels:['1 Bintang','2','3','4','5 Bintang'],
    datasets:[{ label:'Jumlah review', data:[s['1'],s['2'],s['3'],s['4'],s['5']],
      backgroundColor:[COL.red,COL.org,COL.gray,'#a3e635',COL.lime], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:grid} } });
}

// 2) Score distribution kedua (di section ringkasan)
function chartScoreDist2() {
  const s = D.score_dist || {};
  make('chartScoreDist2', { type:'bar', data:{
    labels:['1','2','3','4','5'],
    datasets:[{ label:'Jumlah review', data:[s['1'],s['2'],s['3'],s['4'],s['5']],
      backgroundColor:[COL.red,COL.org,COL.gray,'#a3e635',COL.lime], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:grid} } });
}

// 3) Jumlah review per kategori
function chartCategory() {
  const c = (D.category_counts||[]);
  make('chartCategory', { type:'bar', data:{
    labels:c.map(x=>x.category), datasets:[{ label:'Review relevan', data:c.map(x=>x.count),
      backgroundColor:'rgba(155,93,229,0.75)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:gridY} } });
}

// 4) Tren waktu volume & distress
function chartTimeline() {
  const t = D.timeline || {labels:[]};
  make('chartTimeline', { type:'line', data:{ labels:t.labels, datasets:[
    { label:'Total review', data:t.total, borderColor:COL.pur, backgroundColor:'rgba(155,93,229,0.08)', tension:0.35, fill:true, pointRadius:0, borderWidth:2 },
    { label:'Kategori pinjol', data:t.pinjol, borderColor:COL.lime, backgroundColor:'rgba(184,255,60,0.06)', tension:0.35, fill:true, pointRadius:0, borderWidth:2 },
    { label:'Sinyal distress', data:t.distress, borderColor:COL.red, backgroundColor:'rgba(248,113,113,0.06)', tension:0.35, fill:true, pointRadius:0, borderWidth:2 },
  ]}, options:{ ...chartDefaults, scales:{x:{...grid, ticks:{color:COL.gray, maxTicksLimit:10}}, y:grid} } });
}

// 5) Analisis perilaku
function chartBehavior() {
  const b = (D.behavior||[]);
  make('chartBehavior', { type:'bar', data:{
    labels:b.map(x=>x.label), datasets:[{ label:'Jumlah review', data:b.map(x=>x.count),
      backgroundColor:'rgba(184,255,60,0.75)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:gridY} } });
}

// 6) Kata kunci galbay
function chartKeywords() {
  const k = (D.galbay_keywords||[]).slice(0, 12);
  make('chartKeywords', { type:'bar', data:{
    labels:k.map(x=>x.label), datasets:[{ label:'Frekuensi', data:k.map(x=>x.count),
      backgroundColor:'rgba(249,115,22,0.8)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:gridY} } });
}

// 7) Metrik evaluasi model
function chartModel() {
  const mo = D.model || {};
  make('chartModel', { type:'bar', data:{
    labels:['Accuracy','Precision','Recall','F1-Score'],
    datasets:[{ label:'Skor (%)', data:[mo.accuracy*100, mo.precision*100, mo.recall*100, mo.f1*100].map(v=>+v.toFixed(1)),
      backgroundColor:[COL.lime,COL.pur,COL.blu,COL.grn], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:{...grid,max:100}} } });
}

// 8) Sentimen per kategori
function chartSentimentCat() {
  const c = (D.cat_stats||[]);
  make('chartSentimentCat', { type:'bar', data:{
    labels:c.map(x=>x.category), datasets:[
      { label:'% Negatif', data:c.map(x=>x.neg_pct), backgroundColor:'rgba(248,113,113,0.8)', borderRadius:5 },
      { label:'% Positif', data:c.map(x=>x.pos_pct), backgroundColor:'rgba(184,255,60,0.8)', borderRadius:5 },
    ]
  }, options:{ ...chartDefaults, scales:{x:{...grid, ticks:{color:COL.text, font:{size:10}}}, y:{...grid, max:100}} } });
}

// 9) Top aplikasi rasio negatif
function chartTopApps() {
  const a = (D.top_neg_apps||[]);
  make('chartTopApps', { type:'bar', data:{
    labels:a.map(x=>x.app), datasets:[{ label:'% negatif', data:a.map(x=>x.neg_pct),
      backgroundColor:'rgba(248,113,113,0.8)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:{...grid,max:100},y:gridY} } });
}

// 10) Donut chart distribusi prediksi model
function chartSentimentDist() {
  const c = (D.model || {}).confusion || {};
  const tp = c.TP || 0, tn = c.TN || 0, fp = c.FP || 0, fn = c.FN || 0;
  const correct = tp + tn;
  const wrong = fp + fn;
  make('chartSentimentDist', { type:'doughnut', data:{
    labels:['Prediksi Benar', 'Prediksi Salah'],
    datasets:[{
      data:[correct, wrong],
      backgroundColor:['rgba(184,255,60,0.85)', 'rgba(248,113,113,0.7)'],
      borderColor:['rgba(184,255,60,1)', 'rgba(248,113,113,1)'],
      borderWidth:2,
      hoverOffset:8
    }]
  }, options:{
    responsive:true, maintainAspectRatio:false,
    cutout:'68%',
    plugins:{
      legend:{ position:'bottom', labels:{ color:COL.text, font:{family:'Inter',size:13}, padding:14, boxWidth:14 } },
      tooltip:{ backgroundColor:'#120038', borderColor:'rgba(155,93,229,0.4)', borderWidth:1, titleColor:'#f0eaff', bodyColor:COL.text, padding:12,
        callbacks:{ label:(ctx)=>{ const v=ctx.parsed, total=correct+wrong; const pct=total>0?(v/total*100).toFixed(1):0; return ` ${ctx.label}: ${v.toLocaleString('id-ID')} (${pct}%)`; } } }
    }
  }});
}

// 11) Wordcloud bar horizontal
function chartWordcloud() {
  const k = (D.galbay_keywords || []).slice(0, 15);
  if (!k.length) return;
  const sorted = k.slice().sort((a,b)=>a.count-b.count);
  const maxCount = Math.max(...sorted.map(x=>x.count));
  make('chartWordcloud', { type:'bar', data:{
    labels: sorted.map(x=>x.label),
    datasets:[{
      label:'Frekuensi',
      data: sorted.map(x=>x.count),
      backgroundColor: sorted.map(x=>{
        const intensity = x.count / maxCount;
        const r = Math.round(248 - (248-184)*intensity);
        const g = Math.round(113 + (255-113)*intensity);
        const b = Math.round(113 + (60-113)*intensity);
        return `rgba(${r},${g},${b},0.85)`;
      }),
      borderRadius:4
    }]
  }, options:{
    ...chartDefaults, indexAxis:'y',
    plugins:{...chartDefaults.plugins, legend:{display:false}},
    scales:{x:grid, y:{...gridY, ticks:{...gridY.ticks, font:{size:12, weight:'500'}}}}
  }});
}

// 12) Render top 10 apps table
function renderTopAppsTable() {
  const tbody = document.querySelector('#topAppsTable tbody');
  if (!tbody) return;
  const apps = (D.top_neg_apps || []).slice(0, 10);
  if (!apps.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">Data belum tersedia</td></tr>';
    return;
  }
  const maxRatio = Math.max(...apps.map(a=>a.neg_pct||0), 1);
  tbody.innerHTML = apps.map((a, i) => {
    const ratio = a.neg_pct || 0;
    const barW = Math.max(20, Math.round((ratio / maxRatio) * 80));
    const cls = ratio >= 70 ? 'neg-high' : (ratio >= 40 ? 'neg-med' : 'neg-low');
    const avgScore = a.avg_score != null ? a.avg_score.toFixed(2) : '-';
    const total = a.n != null ? a.n.toLocaleString('id-ID') : '-';
    const neg = a.n != null ? Math.round(a.n * ratio / 100).toLocaleString('id-ID') : '-';
    return `<tr>
      <td><span class="rank-badge">${i+1}</span></td>
      <td style="color:var(--text-primary);font-weight:600;">${a.app || '-'}</td>
      <td>${a.category || '-'}</td>
      <td>${total}</td>
      <td>${neg}</td>
      <td><span class="ratio-bar" style="width:${barW}px"></span><span class="${cls}">${ratio.toFixed(1)}%</span></td>
      <td>${avgScore}</td>
    </tr>`;
  }).join('');
}
