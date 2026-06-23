// ============================================================
// Galbay Predictor - Dashboard logic (data asli hasil scraping + modelling)
// Data di-load dari data.js (window.GALBAY_DATA)
// ============================================================
const D = window.GALBAY_DATA || {};
const COL = { lime:'#b8ff3c', pur:'#9b5de5', violet:'#6a0dad', red:'#f87171', org:'#f97316', blu:'#3b82f6', grn:'#4ade80', gray:'#6b5e80', text:'#a89ac0' };

document.addEventListener('DOMContentLoaded', () => {
  fillNumbers();
  if (window.Chart) initCharts();
  renderTopAppsTable();
  initAnimations();
  initNavHighlight();
  initCounters();
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

// ── NAV HIGHLIGHT (topbar pill, auto-detect section) ──
function initNavHighlight() {
  const sections = document.querySelectorAll('section[id]');
  const navPills = document.querySelectorAll('.nav-pill[data-section]');
  if (!sections.length || !navPills.length) return;

  // Map section ke group nav (topbar 4 menu utama)
  // ringkasan -> ringkasan
  // datamining, model, kritis -> analisis
  // inovasi, bmc, risiko -> bmc
  // kesimpulan -> kesimpulan
  const groupMap = {
    ringkasan: 'ringkasan',
    datamining: 'analisis',
    model: 'analisis',
    kritis: 'analisis',
    inovasi: 'bmc',
    bmc: 'bmc',
    risiko: 'bmc',
    kesimpulan: 'kesimpulan',
  };

  function setActive(groupKey) {
    navPills.forEach(n => n.classList.toggle('active', n.dataset.section === groupKey));
  }

  // Set initial dari hash
  const hash = (window.location.hash || '').replace('#', '');
  if (hash && groupMap[hash]) setActive(groupMap[hash]);

  // Pakai scroll-based detection: section yang paling dominan di viewport
  let lastVisible = null;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        lastVisible = entry.target.id;
      }
    });
    if (lastVisible && groupMap[lastVisible]) {
      setActive(groupMap[lastVisible]);
    }
  }, { threshold: 0.15, rootMargin: '-80px 0px -50% 0px' });
  sections.forEach(s => observer.observe(s));

  // Click handler: set active langsung + hash update
  navPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const key = pill.dataset.section;
      if (groupMap[key] || key) {
        // Tentukan section target dari group
        let target = key;
        if (key === 'analisis') target = 'datamining';
        else if (key === 'bmc') target = 'bmc';
        setActive(key);
        // smooth scroll ke section pertama dalam group
        const el = document.getElementById(target);
        if (el) {
          window.scrollTo({ top: el.offsetTop - 80, behavior: 'smooth' });
        }
      }
    });
  });
}

// ── COUNTER ANIMATION ──
function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
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
  const els = document.querySelectorAll('.card, .chart-card, .bmc-block, .timeline-item, .metric-card');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => { entry.target.style.opacity = '1'; entry.target.style.transform = 'translateY(0)'; }, i * 50);
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

function initCharts() {
  Chart.defaults.color = COL.text;
  chartScoreDist();
  chartScoreDist2();
  chartCategory();
  chartTimeline();
  chartBehavior();
  chartKeywords();
  chartWordcloud();
  chartSentimentCat();
  chartTopApps();
  chartSentimentDist();
  chartModel();
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

// 2) Jumlah review per kategori
function chartCategory() {
  const c = (D.category_counts||[]);
  make('chartCategory', { type:'bar', data:{
    labels:c.map(x=>x.category), datasets:[{ label:'Review relevan', data:c.map(x=>x.count),
      backgroundColor:'rgba(155,93,229,0.75)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:gridY} } });
}

// 3) Tren waktu volume & distress
function chartTimeline() {
  const t = D.timeline || {labels:[]};
  make('chartTimeline', { type:'line', data:{ labels:t.labels, datasets:[
    { label:'Total review relevan', data:t.total, borderColor:COL.pur, backgroundColor:'rgba(155,93,229,0.08)', tension:0.35, fill:true, pointRadius:0, borderWidth:2 },
    { label:'Kategori pinjol', data:t.pinjol, borderColor:COL.lime, backgroundColor:'rgba(184,255,60,0.06)', tension:0.35, fill:true, pointRadius:0, borderWidth:2 },
    { label:'Sinyal distress galbay', data:t.distress, borderColor:COL.red, backgroundColor:'rgba(248,113,113,0.06)', tension:0.35, fill:true, pointRadius:0, borderWidth:2 },
  ]}, options:{ ...chartDefaults, scales:{x:{...grid, ticks:{color:COL.gray, maxTicksLimit:10}}, y:grid} } });
}

// 4) Analisis perilaku (kategori bermakna)
function chartBehavior() {
  const b = (D.behavior||[]);
  make('chartBehavior', { type:'bar', data:{
    labels:b.map(x=>x.label), datasets:[{ label:'Jumlah review', data:b.map(x=>x.count),
      backgroundColor:'rgba(184,255,60,0.75)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:gridY} } });
}

// 5) Kata kunci galbay
function chartKeywords() {
  const k = (D.galbay_keywords||[]);
  make('chartKeywords', { type:'bar', data:{
    labels:k.map(x=>x.label), datasets:[{ label:'Frekuensi kemunculan', data:k.map(x=>x.count),
      backgroundColor:'rgba(249,115,22,0.8)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:gridY} } });
}

// 6) Sentimen per kategori (negatif vs positif)
function chartSentimentCat() {
  const c = (D.cat_stats||[]);
  make('chartSentimentCat', { type:'bar', data:{
    labels:c.map(x=>x.category), datasets:[
      { label:'% Negatif (skor 1-2)', data:c.map(x=>x.neg_pct), backgroundColor:'rgba(248,113,113,0.8)', borderRadius:5 },
      { label:'% Positif (skor 4-5)', data:c.map(x=>x.pos_pct), backgroundColor:'rgba(184,255,60,0.8)', borderRadius:5 },
    ]
  }, options:{ ...chartDefaults, scales:{x:{...grid, ticks:{color:COL.text, font:{size:10}}}, y:{...grid, max:100}} } });
}

// 7) Top aplikasi rasio negatif tertinggi
function chartTopApps() {
  const a = (D.top_neg_apps||[]);
  make('chartTopApps', { type:'bar', data:{
    labels:a.map(x=>x.app), datasets:[{ label:'% review negatif', data:a.map(x=>x.neg_pct),
      backgroundColor:'rgba(248,113,113,0.8)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:{...grid,max:100},y:gridY} } });
}

// 8) Metrik evaluasi model
function chartModel() {
  const mo = D.model || {};
  make('chartModel', { type:'bar', data:{
    labels:['Accuracy','Precision','Recall','F1-Score'],
    datasets:[{ label:'Skor (%)', data:[mo.accuracy*100, mo.precision*100, mo.recall*100, mo.f1*100].map(v=>+v.toFixed(1)),
      backgroundColor:[COL.lime,COL.pur,COL.blu,COL.grn], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:{...grid,max:100}} } });
}

// 9) Score distribution kedua (di section ringkasan)
function chartScoreDist2() {
  const s = D.score_dist || {};
  make('chartScoreDist2', { type:'bar', data:{
    labels:['1','2','3','4','5'],
    datasets:[{ label:'Jumlah review', data:[s['1'],s['2'],s['3'],s['4'],s['5']],
      backgroundColor:[COL.red,COL.org,COL.gray,'#a3e635',COL.lime], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}}, scales:{x:grid,y:grid} } });
}

// 10) Donut chart distribusi prediksi model (TP/TN/FP/FN)
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

// 11) Wordcloud bar horizontal — 15 kata kunci paling dominan
function chartWordcloud() {
  const k = (D.galbay_keywords || []).slice(0, 15);
  if (!k.length) return;
  // Sort ascending agar yang paling banyak di atas
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

// 12) Render top 10 apps table dari data
function renderTopAppsTable() {
  const tbody = document.querySelector('#topAppsTable tbody');
  if (!tbody) return;
  const apps = (D.top_neg_apps || []).slice(0, 10);
  if (!apps.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">Data belum tersedia</td></tr>';
    return;
  }
  // Cari max ratio untuk bar
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
