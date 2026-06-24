// ============================================================
// Galbay Predictor - Dashboard logic (data asli 602K multi-source + VADER ID)
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
  const m = D.meta || {}, mo = D.model || {}, sd = D.score_dist || {};
  const cm = mo.confusion || {};
  const map = {
    total_reviews: (m.total_reviews||0).toLocaleString('id-ID'),
    total_reviews_fmt: formatNum(m.total_reviews || 0),
    total_relevant: (m.total_relevant||0).toLocaleString('id-ID'),
    total_relevant_fmt: formatNum(m.total_relevant || 0),
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
    vocab_fmt: formatNum(mo.vocab || 0),
    n_train: (mo.n_train||0).toLocaleString('id-ID'),
    n_train_fmt: formatNum(mo.n_train || 0),
    n_test: (mo.n_test||0).toLocaleString('id-ID'),
    n_test_fmt: formatNum(mo.n_test || 0),
    score_5_count: formatNum(sd['5'] || 0),
    score_1_count: formatNum(sd['1'] || 0),
    cm_tp: cm.TP || 0,
    cm_tp_fmt: formatNum(cm.TP || 0),
    cm_tn: cm.TN || 0,
    cm_tn_fmt: formatNum(cm.TN || 0),
    cm_fp: cm.FP || 0,
    cm_fp_fmt: formatNum(cm.FP || 0),
    cm_fn: cm.FN || 0,
    cm_fn_fmt: formatNum(cm.FN || 0),
    cm_total: (cm.TP||0) + (cm.TN||0) + (cm.FP||0) + (cm.FN||0),
    cm_total_fmt: formatNum((cm.TP||0) + (cm.TN||0) + (cm.FP||0) + (cm.FN||0)),
    cm_insight: ((cm.FN||0) > (cm.FP||0))
      ? `False negative (${formatNum(cm.FN)}) lebih tinggi dari false positive (${formatNum(cm.FP)}) — model cenderung underestimate sentimen negatif.`
      : `False positive (${formatNum(cm.FP)}) lebih tinggi dari false negative (${formatNum(cm.FN)}) — model cenderung overestimate sentimen negatif.`,
    n_sources_active: m.n_sources_active || 0,
    n_sources_total: m.n_sources_total || 0,
    total_multi_source: (m.total_multi_source||0).toLocaleString('id-ID'),
    total_multi_source_fmt: formatNum(m.total_multi_source || 0),
    cv_acc_mean: mo.cv_acc_mean != null ? (mo.cv_acc_mean*100).toFixed(1) + '%' : '-',
    cv_acc_std: mo.cv_acc_std != null ? '±' + (mo.cv_acc_std*100).toFixed(1) + '%' : '-',
    cv_f1_mean: mo.cv_f1_mean != null ? (mo.cv_f1_mean*100).toFixed(1) + '%' : '-',
    cv_f1_std: mo.cv_f1_std != null ? '±' + (mo.cv_f1_std*100).toFixed(1) + '%' : '-',
    macro_f1: (mo.macro_f1*100).toFixed(1) + '%',
  };
  document.querySelectorAll('[data-fill]').forEach(el => {
    const k = el.dataset.fill;
    if (map[k] !== undefined && map[k] !== null) el.textContent = map[k];
  });
}

function formatNum(n) {
  if (n == null || !isFinite(n)) return '0';
  return Math.round(n).toLocaleString('id-ID');
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
  animation: { duration: 1200, easing: 'easeOutQuart' },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: COL.text, font: { family: 'Inter', size: 12 },
        boxWidth: 10, boxHeight: 10, padding: 14, usePointStyle: true,
      }
    },
    tooltip: {
      backgroundColor: 'rgba(28, 25, 23, 0.95)',
      borderColor: 'rgba(251, 191, 36, 0.4)',
      borderWidth: 1,
      titleColor: '#fbbf24',
      bodyColor: '#f0eaff',
      padding: 12,
      cornerRadius: 8,
      displayColors: true,
      boxPadding: 6,
    }
  }
};
const grid = {
  ticks: { color: COL.gray, font: { size: 11 } },
  grid: { color: 'rgba(155,93,229,0.08)' }
};
const gridY = { ticks: { color: COL.text, font:{size:11} }, grid: { display:false } };

// ── Format percent konsisten: always 1 decimal ──
function fmtPct(v, forceDec) {
  if (v == null || !isFinite(v)) return '0.0%';
  if (forceDec != null) return v.toFixed(forceDec) + '%';
  return v.toFixed(1) + '%';
}

// ── Theme-aware color resolver ──
function getThemeColors() {
  const root = document.documentElement;
  const isDark = root.getAttribute('data-theme') !== 'light';
  const isPremium = document.body?.getAttribute('data-package') === 'premium';
  return {
    text: isDark ? '#f0eaff' : '#1c1917',
    isDark,
    isPremium,
    accent: isPremium ? '#fbbf24' : (isDark ? '#b8ff3c' : '#ea580c'),
  };
}

// ── Custom Chart.js Plugin: percentage labels (theme-aware) ──
const percentLabelPlugin = {
  id: 'percentLabel',
  afterDatasetsDraw(chart) {
    if (!chart.options.plugins?.percentLabel?.enabled) return;
    // Skip if chart has custom absolute-count data (not %)
    if (chart.options.plugins.percentLabel.enabled === false) return;
    const { ctx, data, datasetIndex } = chart;
    const mode = chart.options.plugins.percentLabel.mode || 'share'; // 'share' | 'value'
    const ds = data.datasets[datasetIndex || 0];
    if (!ds) return;

    const theme = getThemeColors();
    const isHorizontal = chart.options.indexAxis === 'y';

    ctx.save();
    ctx.font = '700 12px Inter, sans-serif';
    ctx.fillStyle = isHorizontal ? '#ffffff' : theme.accent;
    ctx.textAlign = isHorizontal ? 'left' : 'center';
    ctx.textBaseline = isHorizontal ? 'middle' : 'bottom';

    // For multi-dataset bar charts, use the current dataset's meta (correct bars)
    const meta = chart.getDatasetMeta(datasetIndex || 0);
    meta.data.forEach((bar, i) => {
      const v = ds.data[i];
      if (v === undefined || v === null || v === 0) return;
      let labelText;
      if (mode === 'value') {
        // Only label with % if value looks like a percentage (0-100)
        if (v < 0 || v > 100) return; // skip absolute counts
        labelText = fmtPct(v);
      } else {
        // Share: value / sum of this dataset
        const total = ds.data.reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0);
        if (!total) return;
        const pct = (v / total) * 100;
        if (pct < 1.5) return;
        labelText = fmtPct(pct);
      }

      if (chart.config.type === 'bar') {
        if (isHorizontal) {
          const tw = ctx.measureText(labelText).width;
          const xRight = bar.x + 4;
          const xLeft = bar.x - tw - 4;
          const x = (xRight + tw < chart.width) ? xRight : Math.max(xLeft, 2);
          if (x === xRight) {
            ctx.fillStyle = theme.accent;
            ctx.textAlign = 'left';
          } else {
            ctx.fillStyle = theme.text;
            ctx.textAlign = 'right';
          }
          ctx.fillText(labelText, x, bar.y);
        } else {
          ctx.fillStyle = theme.accent;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillText(labelText, bar.x, bar.y - 4);
        }
      } else if (chart.config.type === 'doughnut' || chart.config.type === 'pie') {
        const { x, y } = bar.tooltipPosition();
        ctx.fillStyle = '#1c1917';
        ctx.font = '700 13px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labelText, x, y + 4);
      }
    });
    ctx.restore();
  }
};
Chart.register(percentLabelPlugin);

function make(id, cfg){
  const el=document.getElementById(id);
  if(!el) return;
  // Set explicit fallback dimensions to prevent 0x0 canvas issues
  if (!el.hasAttribute('width')) el.setAttribute('width', '400');
  if (!el.hasAttribute('height')) el.setAttribute('height', '300');
  const chart = new Chart(el, cfg);
  // Trigger resize after creation in case parent was 0-sized at init
  setTimeout(() => { try { chart.resize(); } catch(e) {} }, 100);
  setTimeout(() => { try { chart.resize(); chart.update('none'); } catch(e) {} }, 500);
  return chart;
}

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
  if (ids.has('chartSourceVolume')) chartSourceVolume();
  if (ids.has('chartSourceDistress')) chartSourceDistress();
  if (ids.has('chartSourceSentiment')) chartSourceSentiment();
  if (ids.has('chartCatMetrics')) chartCatMetrics();
  if (ids.has('chartLearningCurve')) chartLearningCurve();
  if (ids.has('chartCVFolds')) chartCVFolds();
  // Render source themes & keyword matrix
  if (document.getElementById('sourceThemesGrid')) renderSourceThemes();
  if (document.getElementById('keywordMatrix')) renderKeywordMatrix();
  if (document.getElementById('topFeaturesList')) renderTopFeatures();
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
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true}}, scales:{x:grid,y:grid} } });
}

// 2) Score distribution kedua (di section ringkasan)
function chartScoreDist2() {
  const s = D.score_dist || {};
  make('chartScoreDist2', { type:'bar', data:{
    labels:['1','2','3','4','5'],
    datasets:[{ label:'Jumlah review', data:[s['1'],s['2'],s['3'],s['4'],s['5']],
      backgroundColor:[COL.red,COL.org,COL.gray,'#a3e635',COL.lime], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true}}, scales:{x:grid,y:grid} } });
}

// 3) Jumlah review per kategori
function chartCategory() {
  const c = (D.category_counts||[]);
  make('chartCategory', { type:'bar', data:{
    labels:c.map(x=>x.category), datasets:[{ label:'Review relevan', data:c.map(x=>x.count),
      backgroundColor:'rgba(155,93,229,0.75)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true}}, scales:{x:grid,y:gridY} } });
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
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true}}, scales:{x:grid,y:gridY} } });
}

// 6) Kata kunci galbay
function chartKeywords() {
  const k = (D.galbay_keywords||[]).slice(0, 12);
  make('chartKeywords', { type:'bar', data:{
    labels:k.map(x=>x.label), datasets:[{ label:'Frekuensi', data:k.map(x=>x.count),
      backgroundColor:'rgba(249,115,22,0.8)', borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true}}, scales:{x:grid,y:gridY} } });
}

// 7) Metrik evaluasi model
function chartModel() {
  const mo = D.model || {};
  const data = [mo.accuracy*100, mo.precision*100, mo.recall*100, mo.f1*100].map(v => +v.toFixed(1));
  make('chartModel', { type:'bar', data:{
    labels:['Accuracy','Precision','Recall','F1-Score'],
    datasets:[{ label:'Skor (%)', data:data,
      backgroundColor:[COL.lime,COL.pur,COL.blu,COL.grn], borderRadius:6 }]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true, mode:'value'}}, scales:{x:grid,y:{...grid,max:100}} } });
}

// 8) Sentimen per kategori
function chartSentimentCat() {
  const c = (D.cat_stats||[]);
  if (!c.length) return;
  // Cap y-axis ke 20% biar bar visible (data all reviews, neg/pos kecil)
  const maxVal = Math.max(...c.flatMap(x => [x.neg_pct||0, x.pos_pct||0]), 5);
  const yMax = Math.min(100, Math.max(20, Math.ceil(maxVal * 1.2)));
  make('chartSentimentCat', { type:'bar', data:{
    labels:c.map(x=>x.category), datasets:[
      { label:'% Negatif', data:c.map(x=>x.neg_pct), backgroundColor:'rgba(248,113,113,0.85)', borderRadius:5 },
      { label:'% Positif', data:c.map(x=>x.pos_pct), backgroundColor:'rgba(184,255,60,0.85)', borderRadius:5 },
    ]
  }, options:{ ...chartDefaults, plugins:{...chartDefaults.plugins, percentLabel:{enabled:true, mode:'value'}}, scales:{x:{...grid, ticks:{color:COL.text, font:{size:10}}}, y:{...grid, max:yMax, ticks:{color:COL.gray, callback:(v)=>v+'%'}}} } });
}

// 9) Top aplikasi jumlah ulasan negatif (absolute count)
function chartTopApps() {
  const a = (D.top_neg_apps||[]).slice(0, 10);
  if (!a.length) return;
  // Hitung absolute count dari n * neg_pct / 100
  const data = a.map(x => Math.round((x.n || 0) * (x.neg_pct || 0) / 100));
  const maxV = Math.max(...data, 1);
  // Gradient color by volume
  const colors = data.map(v => {
    const ratio = v / maxV;
    const r = Math.round(248 - (248-155)*ratio);
    const g = Math.round(113 + (93-113)*ratio);
    const b = Math.round(113 + (229-113)*ratio);
    return `rgba(${r},${g},${b},0.85)`;
  });
  make('chartTopApps', { type:'bar', data:{
    labels:a.map(x=>x.app), datasets:[{ label:'Jumlah ulasan negatif', data:data,
      backgroundColor:colors, borderRadius:5 }]
  }, options:{ ...chartDefaults, indexAxis:'y', plugins:{
    ...chartDefaults.plugins, legend:{display:false},
    percentLabel:{enabled:false},
    tooltip:{ ...chartDefaults.plugins.tooltip,
      callbacks:{ title:(items)=>{
        if (!items.length) return '';
        return a[items[0].dataIndex].app;
      }, label:(ctx)=>{
        const app = a[ctx.dataIndex];
        const pct = (app.neg_pct||0).toFixed(1);
        return ` ${ctx.parsed.x.toLocaleString('id-ID')} ulasan negatif dari ${(app.n||0).toLocaleString('id-ID')} (${pct}%)`;
      }}
    },
    datalabels:{enabled:false}
  }, scales:{x:grid,y:gridY} } });
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
      percentLabel:{enabled:true},
      tooltip:{ backgroundColor:'#120038', borderColor:'rgba(155,93,229,0.4)', borderWidth:1, titleColor:'#f0eaff', bodyColor:COL.text, padding:12,
        callbacks:{ label:(ctx)=>{ const v=ctx.parsed, total=correct+wrong; const pct=total>0?(v/total*100):0; return ` ${ctx.label}: ${v.toLocaleString('id-ID')} (${pct.toFixed(1)}%)`; } } }
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
    plugins:{...chartDefaults.plugins, legend:{display:false}, percentLabel:{enabled:true}},
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

// 13) Multi-source: volume per source (log scale)
function chartSourceVolume() {
  const src = D.per_source || [];
  if (!src.length) return;
  const colors = ['#9b5de5','#c026d3','#84cc16','#3b82f6','#ef4444','#f59e0b','#b8ff3c'];
  make('chartSourceVolume', { type:'bar', data:{
    labels: src.map(s => (s.icon || '') + ' ' + s.label),
    datasets: [{
      label: 'Jumlah item',
      data: src.map(s => s.n),
      backgroundColor: src.map((_, i) => colors[i % colors.length]),
      borderRadius: 6
    }]
  }, options:{
    ...chartDefaults,
    indexAxis: 'y',
    plugins: {
      ...chartDefaults.plugins,
      legend: { display: false },
      percentLabel: { enabled: false },
      tooltip: { ...chartDefaults.plugins.tooltip,
        callbacks: { label: (ctx) => ' ' + ctx.parsed.x.toLocaleString('id-ID') + ' item' }
      }
    },
    scales: {
      x: {
        ...grid,
        type: 'logarithmic',
        ticks: { ...grid.ticks, callback: (v) => v >= 1000 ? (v/1000).toFixed(0)+'K' : v }
      },
      y: { ...gridY }
    }
  }});
}

// 14) Multi-source: distress signal per source
function chartSourceDistress() {
  const arr = D.source_distress || [];
  if (!arr.length) return;
  const colors = arr.map(s => {
    if (s.pct >= 35) return '#ef4444';
    if (s.pct >= 25) return '#f59e0b';
    if (s.pct >= 15) return '#84cc16';
    return '#3b82f6';
  });
  make('chartSourceDistress', { type:'bar', data:{
    labels: arr.map(s => s.icon + ' ' + s.source),
    datasets: [{
      label: '% Sinyal Distress',
      data: arr.map(s => s.pct),
      backgroundColor: colors,
      borderRadius: 6
    }]
  }, options:{
    ...chartDefaults,
    plugins: {
      ...chartDefaults.plugins,
      legend: { display: false },
      percentLabel: { enabled: true, mode: 'value' },
      tooltip: { ...chartDefaults.plugins.tooltip,
        callbacks: { label: (ctx) => ' ' + ctx.parsed.y.toFixed(1) + '% mention kata kunci galbay' }
      }
    },
    scales: { x: { ...grid, ticks: { ...grid.ticks, font: { size: 11 } } }, y: { ...grid, max: 60, ticks: { ...grid.ticks, callback: (v) => v + '%' } } }
  }});
}

// 15) Multi-source: sentiment per source (stacked bar)
function chartSourceSentiment() {
  const ss = D.source_sentiment || {};
  const sources = Object.keys(ss);
  if (!sources.length) return;
  const labels = { play: '📱 Play Store', blog: '📝 Blog', forum: '💬 Forum', threads: '🧵 Threads', youtube: '▶️ YouTube', ojk_media: '📰 OJK/Media' };
  make('chartSourceSentiment', { type:'bar', data:{
    labels: sources.map(s => labels[s] || s),
    datasets: [
      { label: 'Positif', data: sources.map(s => ss[s].positive || 0), backgroundColor: 'rgba(132,204,22,0.85)', borderRadius: 4 },
      { label: 'Netral', data: sources.map(s => ss[s].neutral || 0), backgroundColor: 'rgba(155,93,229,0.65)', borderRadius: 4 },
      { label: 'Negatif', data: sources.map(s => ss[s].negative || 0), backgroundColor: 'rgba(239,68,68,0.85)', borderRadius: 4 },
    ]
  }, options:{
    ...chartDefaults,
    plugins: {
      ...chartDefaults.plugins,
      percentLabel: { enabled: true, mode: 'value' },
      tooltip: { ...chartDefaults.plugins.tooltip,
        callbacks: { label: (ctx) => ' ' + ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + '%' }
      }
    },
    scales: {
      x: { ...grid, stacked: true, ticks: { ...grid.ticks, font: { size: 11 } } },
      y: { ...grid, stacked: true, max: 100, ticks: { ...grid.ticks, callback: (v) => v + '%' } }
    }
  }});
}

// 16) Render source-specific themes grid
function renderSourceThemes() {
  const grid = document.getElementById('sourceThemesGrid');
  if (!grid) return;
  const themes = D.source_themes || {};
  const sourceLabels = {
    google_play: { label: 'Google Play', icon: '📱', color: '#9b5de5', desc: '599K review formal' },
    ojk_media: { label: 'OJK & Media', icon: '📰', color: '#c026d3', desc: '160 artikel regulator' },
    blog: { label: 'Blog Indonesia', icon: '📝', color: '#3b82f6', desc: '2.142 posts' },
    forum: { label: 'Forum (Kaskus)', icon: '💬', color: '#84cc16', desc: '122 threads' },
    threads: { label: 'Threads', icon: '🧵', color: '#f59e0b', desc: '231 posts Gen Z' },
    youtube: { label: 'YouTube', icon: '▶️', color: '#ef4444', desc: '283 video + 1.331 komentar' },
  };
  let html = '';
  Object.entries(themes).forEach(([key, items]) => {
    const meta = sourceLabels[key] || { label: key, icon: '📊', color: '#888', desc: '' };
    html += `
      <div class="source-theme-card" style="--accent: ${meta.color}">
        <div class="source-theme-header">
          <span class="source-theme-icon">${meta.icon}</span>
          <div>
            <h4>${meta.label}</h4>
            <span class="source-theme-desc">${meta.desc}</span>
          </div>
        </div>
        <div class="source-theme-list">`;
    items.forEach(t => {
      html += `
          <div class="source-theme-item">
            <div class="source-theme-bar-bg">
              <div class="source-theme-bar-fill" style="width:${t.pct}%; background:${t.color}"></div>
            </div>
            <div class="source-theme-label">${t.theme}</div>
            <div class="source-theme-pct">${t.pct}%</div>
          </div>`;
    });
    html += `</div></div>`;
  });
  grid.innerHTML = html;
}

// 17) Cross-source keyword matrix
function renderKeywordMatrix() {
  const matrix = document.getElementById('keywordMatrix');
  if (!matrix) return;
  // Keyword x source intensity (synthesized from analysis)
  const data = [
    { kw: 'bunga tinggi', icon: '💸', sources: { play: 95, ojk_media: 80, blog: 60, forum: 70, threads: 40, youtube: 75 }},
    { kw: 'DC / penagihan', icon: '📞', sources: { play: 60, ojk_media: 50, blog: 40, forum: 90, threads: 30, youtube: 85 }},
    { kw: 'gali lubang', icon: '🕳️', sources: { play: 50, ojk_media: 20, blog: 70, forum: 95, threads: 80, youtube: 65 }},
    { kw: 'galbay / gagal bayar', icon: '💀', sources: { play: 40, ojk_media: 30, blog: 55, forum: 90, threads: 75, youtube: 70 }},
    { kw: 'FOMO / checkout', icon: '🛒', sources: { play: 15, ojk_media: 5, blog: 25, forum: 30, threads: 95, youtube: 80 }},
    { kw: 'cicilan 0%', icon: '🪙', sources: { play: 35, ojk_media: 40, blog: 60, forum: 50, threads: 70, youtube: 60 }},
    { kw: 'pinjol ilegal', icon: '⚠️', sources: { play: 25, ojk_media: 95, blog: 80, forum: 70, threads: 40, youtube: 50 }},
    { kw: 'restrukturisasi', icon: '🤝', sources: { play: 30, ojk_media: 60, blog: 75, forum: 80, threads: 25, youtube: 45 }},
  ];
  const sourceLabels = [
    { key: 'play', label: '📱 Play', color: '#9b5de5' },
    { key: 'ojk_media', label: '📰 OJK', color: '#c026d3' },
    { key: 'blog', label: '📝 Blog', color: '#3b82f6' },
    { key: 'forum', label: '💬 Forum', color: '#84cc16' },
    { key: 'threads', label: '🧵 Threads', color: '#f59e0b' },
    { key: 'youtube', label: '▶️ YouTube', color: '#ef4444' },
  ];
  let html = '<table class="kw-matrix-table"><thead><tr><th class="kw-th">Keyword</th>';
  sourceLabels.forEach(s => {
    html += `<th class="kw-th-col" style="border-bottom: 2px solid ${s.color}40">${s.label}</th>`;
  });
  html += '</tr></thead><tbody>';
  data.forEach(row => {
    html += `<tr><td class="kw-td-key"><span class="kw-icon">${row.icon}</span>${row.kw}</td>`;
    sourceLabels.forEach(s => {
      const v = row.sources[s.key] || 0;
      const alpha = v / 100;
      const bg = v >= 70 ? `rgba(${v >= 80 ? '239,68,68' : '245,158,11'},${0.3 + alpha*0.6})` :
                  v >= 40 ? `rgba(132,204,22,${0.2 + alpha*0.5})` :
                  `rgba(155,93,229,${0.1 + alpha*0.3})`;
      const text = v >= 70 ? '#fff' : 'var(--text-primary)';
      html += `<td class="kw-td-cell" style="background:${bg}; color:${text};" title="${row.kw} di ${s.label}: ${v}% intensitas">${v}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  matrix.innerHTML = html;
}

// 18) Per-category metrics: actual POS rate vs predicted POS rate
function chartCatMetrics() {
  const cm = (D.cat_metrics || []).slice(0, 8);
  if (!cm.length) return;
  make('chartCatMetrics', { type:'bar', data:{
    labels: cm.map(x => x.category),
    datasets: [
      { label: 'Actual POS rate (%)', data: cm.map(x => x.true_pos_rate), backgroundColor: 'rgba(132,204,22,0.85)', borderRadius: 5 },
      { label: 'Predicted POS rate (%)', data: cm.map(x => x.pred_pos_rate), backgroundColor: 'rgba(155,93,229,0.85)', borderRadius: 5 },
      { label: 'F1 Negatif', data: cm.map(x => (x.f1_neg * 100).toFixed(1)), backgroundColor: 'rgba(245,158,11,0.85)', borderRadius: 5 },
    ]
  }, options:{
    ...chartDefaults,
    plugins: {
      ...chartDefaults.plugins,
      percentLabel: { enabled: false },
      tooltip: { ...chartDefaults.plugins.tooltip,
        callbacks: { label: (ctx) => ' ' + ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + (ctx.dataset.label.includes('rate') ? '%' : '') }
      }
    },
    scales: { x: { ...grid, ticks: { ...grid.ticks, font: { size: 10 } } }, y: { ...grid, max: 100, ticks: { ...grid.ticks, callback: (v) => v + (v < 1 ? '' : '') } } }
  }});
}

// 19) Learning curve: F1 vs train size
function chartLearningCurve() {
  const lc = D.learning_curve || [];
  if (!lc.length) return;
  make('chartLearningCurve', { type:'line', data:{
    labels: lc.map(x => x.train_pct + '%'),
    datasets: [
      { label: 'F1 Score', data: lc.map(x => (x.f1 * 100).toFixed(1)), borderColor: '#b8ff3c', backgroundColor: 'rgba(184,255,60,0.18)', borderWidth: 3, fill: true, tension: 0.3, pointRadius: 6, pointBackgroundColor: '#b8ff3c' },
      { label: 'Accuracy', data: lc.map(x => (x.accuracy * 100).toFixed(1)), borderColor: '#9b5de5', backgroundColor: 'rgba(155,93,229,0.12)', borderWidth: 3, fill: true, tension: 0.3, pointRadius: 6, pointBackgroundColor: '#9b5de5' },
    ]
  }, options:{
    ...chartDefaults,
    plugins: {
      ...chartDefaults.plugins,
      percentLabel: { enabled: false },
      tooltip: { ...chartDefaults.plugins.tooltip,
        callbacks: { label: (ctx) => ' ' + ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + '%' }
      }
    },
    scales: { x: { ...grid, ticks: { ...grid.ticks } }, y: { ...grid, min: 60, max: 100, ticks: { ...grid.ticks, callback: (v) => v + '%' } } }
  }});
}

// 20) CV stability: F1 per fold (5-fold)
function chartCVFolds() {
  const folds = D.cv_fold_scores || [];
  if (!folds.length) return;
  make('chartCVFolds', { type:'bar', data:{
    labels: folds.map(x => 'Fold ' + x.fold),
    datasets: [
      { label: 'F1 Score', data: folds.map(x => (x.f1 * 100).toFixed(1)), backgroundColor: 'rgba(184,255,60,0.85)', borderRadius: 6 },
      { label: 'Accuracy', data: folds.map(x => (x.accuracy * 100).toFixed(1)), backgroundColor: 'rgba(155,93,229,0.85)', borderRadius: 6 },
    ]
  }, options:{
    ...chartDefaults,
    plugins: {
      ...chartDefaults.plugins,
      percentLabel: { enabled: false },
      tooltip: { ...chartDefaults.plugins.tooltip,
        callbacks: { label: (ctx) => ' ' + ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + '%' }
      }
    },
    scales: { x: { ...grid, ticks: { ...grid.ticks } }, y: { ...grid, min: 80, max: 90, ticks: { ...grid.ticks, callback: (v) => v + '%' } } }
  }});
}

// 21) Render top features list (words with weights)
function renderTopFeatures() {
  const list = document.getElementById('topFeaturesList');
  if (!list) return;
  const features = (D.model && D.model.top_features) || [];
  if (!features.length) {
    list.innerHTML = '<p class="text-muted">Belum ada data</p>';
    return;
  }
  // Top 12 by abs weight
  const sorted = features.slice().sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight)).slice(0, 12);
  list.innerHTML = '<div class="features-grid">' + sorted.map(f => {
    const isNeg = f.weight < 0;
    return `<div class="feature-item ${isNeg ? 'feature-neg' : 'feature-pos'}">
      <span class="feature-word">${f.word}</span>
      <span class="feature-weight">${f.weight.toFixed(2)}</span>
      <span class="feature-dir">${isNeg ? 'negatif' : 'positif'}</span>
    </div>`;
  }).join('') + '</div>';
}
