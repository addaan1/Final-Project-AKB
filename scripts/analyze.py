# -*- coding: utf-8 -*-
"""
Galbay Predictor - Modelling & Analysis
- Sentiment classifier (Multinomial Naive Bayes from scratch)
- Behavioral (galbay) analysis from matched_categories
- Trend, category, top-apps insights
Outputs: /data/site/data.js  + PNG charts in /data/site/assets/
"""
import pandas as pd, numpy as np, re, json, math, os
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAW = '/data/raw/'
OUT = '/data/site/'
ASSETS = OUT + 'assets/'
os.makedirs(ASSETS, exist_ok=True)
np.random.seed(42)

# ---------- Dark theme for matplotlib ----------
plt.rcParams.update({
    'figure.facecolor': '#120038', 'axes.facecolor': '#120038',
    'savefig.facecolor': '#120038', 'text.color': '#f0eaff',
    'axes.labelcolor': '#a89ac0', 'xtick.color': '#a89ac0', 'ytick.color': '#a89ac0',
    'axes.edgecolor': '#6a0dad', 'font.size': 11, 'axes.titlecolor': '#b8ff3c'
})
LIME='#b8ff3c'; PUR='#9b5de5'; RED='#f87171'; ORG='#f97316'; BLU='#3b82f6'; GRN='#4ade80'

print('Loading data...')
rel = pd.read_csv(RAW+'relevant_only.csv')
pa  = pd.read_csv(RAW+'per_app_summary.csv')
tl  = pd.read_csv(RAW+'timeline.csv')
try:
    nrows_all = sum(1 for _ in open(RAW+'all_reviews.csv', encoding='utf-8')) - 1
except Exception:
    nrows_all = int(pa['n_reviews'].sum())
fnews = pd.read_csv(RAW+'validated_news.csv'); fforum = pd.read_csv(RAW+'validated_forum.csv')

rel['content'] = rel['content'].fillna('').astype(str)

# ================= 1) TEXT PREPROCESS =================
STOP = set('''yang di ke dari dan atau ini itu untuk dengan pada saya aku kamu dia mereka kami kita
ada tidak ga gak ngga nggak engga tdk udah sudah belum lagi juga aja saja kok sih deh dong ya yaa
nya kah pun para per se the a an is are was do does si bang min admin app aplikasi nih tuh gitu gini
bisa bukan kalo kalau karena biar buat dapat dapet jadi jd klo nya banget bgt kan akan masih mau
lah loh org orang tp tapi dr dgn utk yg krn pada oleh sd sampai hingga agar supaya kpd kepada
'''.split())

token_re = re.compile(r"[a-zA-Z]+")
def tok(t):
    return [w for w in token_re.findall(t.lower()) if len(w) > 2 and w not in STOP]

# ================= 2) SENTIMENT LABELS =================
# negative: score 1-2 ; positive: score 4-5 ; drop neutral (3)
d = rel[rel['score'] != 3].copy()
d['label'] = (d['score'] >= 4).astype(int)   # 1=positive, 0=negative
d['tokens'] = d['content'].apply(tok)
d = d[d['tokens'].map(len) > 0].reset_index(drop=True)

# train/test split
idx = np.random.permutation(len(d))
cut = int(len(d)*0.8)
tr_i, te_i = idx[:cut], idx[cut:]
train, test = d.iloc[tr_i], d.iloc[te_i]

# ================= 3) MULTINOMIAL NAIVE BAYES (from scratch) =================
print('Training Naive Bayes...')
MIN_DF = 5
df_counter = Counter()
for toks in train['tokens']:
    df_counter.update(set(toks))
_filtered = [w for w,c in df_counter.items() if c >= MIN_DF]
vocab = {w:i for i,w in enumerate(_filtered)}
V = len(vocab)

cls_word = {0: np.ones(V), 1: np.ones(V)}  # Laplace smoothing
cls_tot  = {0: 0.0, 1: 0.0}
cls_docs = {0: 0, 1: 0}
for toks, lab in zip(train['tokens'], train['label']):
    cls_docs[lab]+=1
    arr = cls_word[lab]
    for w in toks:
        j = vocab.get(w)
        if j is not None:
            arr[j]+=1; cls_tot[lab]+=1
logprior = {c: math.log(cls_docs[c]/len(train)) for c in (0,1)}
loglik = {c: np.log(cls_word[c] / (cls_tot[c] + V)) for c in (0,1)}

def predict(toks):
    s0, s1 = logprior[0], logprior[1]
    for w in toks:
        j = vocab.get(w)
        if j is not None:
            s0 += loglik[0][j]; s1 += loglik[1][j]
    return 1 if s1 >= s0 else 0

preds = test['tokens'].apply(predict).values
y = test['label'].values
TP = int(((preds==1)&(y==1)).sum()); TN = int(((preds==0)&(y==0)).sum())
FP = int(((preds==1)&(y==0)).sum()); FN = int(((preds==0)&(y==1)).sum())
acc = (TP+TN)/len(y)
prec = TP/(TP+FP) if TP+FP else 0
rec = TP/(TP+FN) if TP+FN else 0
f1 = 2*prec*rec/(prec+rec) if prec+rec else 0
print(f'Acc={acc:.3f} Prec={prec:.3f} Rec={rec:.3f} F1={f1:.3f}')

# top predictive words (log-likelihood ratio)
inv = {i:w for w,i in vocab.items()}
ratio = loglik[0] - loglik[1]   # high => negative indicator
order = np.argsort(ratio)
top_neg = [(inv[i], round(float(ratio[i]),2)) for i in order[::-1][:12]]
top_pos = [(inv[i], round(float(-ratio[i]),2)) for i in order[:12]]

# ================= 4) BEHAVIORAL (GALBAY) ANALYSIS =================
rel['mc'] = rel['matched_categories_str'].fillna('')
beh = Counter()
for s in rel['mc']:
    for c in [x.strip() for x in s.split(',') if x.strip()]:
        beh[c]+=1
BEH_LABEL = {
 'produk_fintech':'Diskusi Produk Fintech','bunga_dan_biaya':'Keluhan Bunga & Biaya',
 'tagihan_dan_penagihan':'Tagihan & Penagihan (DC)','psikologi_avoidance':'Psikologi: Menghindar',
 'distress_langsung':'Distress Finansial Langsung','psikologi_regret_stress':'Psikologi: Penyesalan/Stres',
 'psikologi_impulsif':'Psikologi: Impulsif'}
behavior = [{'key':k,'label':BEH_LABEL.get(k,k),'count':int(v)} for k,v in beh.most_common()]

# galbay distress signal = any of these tags
DISTRESS = {'distress_langsung','tagihan_dan_penagihan','psikologi_regret_stress','psikologi_avoidance'}
def is_distress(s):
    return int(any(t in DISTRESS for t in [x.strip() for x in s.split(',')]))
rel['distress'] = rel['mc'].apply(is_distress)

# galbay keyword scan
KW = {'gagal bayar/galbay':r'galbay|gagal bayar','telat/nunggak':r'telat|nunggak|tunggak',
 'denda':r'denda|pinalti|penalti','bunga tinggi':r'bunga',
 'debt collector/DC':r'\bdc\b|debt collector|penagih|nagih',
 'teror/ancam':r'teror|ancam|sebar data|intimidasi','pinjol ilegal':r'ilegal| legal|ojk',
 'gali lubang tutup lubang':r'gali lubang|tutup lubang|pinjam.*bayar'}
content_low = rel['content'].str.lower()
kw_counts = [{'label':k,'count':int(content_low.str.contains(p,regex=True,na=False).sum())} for k,p in KW.items()]
kw_counts.sort(key=lambda x:-x['count'])

# ================= 5) CATEGORY & SENTIMENT BREAKDOWN =================
rel['neg'] = (rel['score']<=2).astype(int)
rel['pos'] = (rel['score']>=4).astype(int)
cat_stats=[]
for c,g in rel.groupby('category'):
    if len(g)>=50:
        cat_stats.append({'category':c,'n':int(len(g)),
          'neg_pct':round(100*g['neg'].mean(),1),'pos_pct':round(100*g['pos'].mean(),1),
          'avg_score':round(g['score'].mean(),2),'distress_pct':round(100*g['distress'].mean(),1)})
cat_stats.sort(key=lambda x:-x['n'])

# top apps by negative rate (min 200 relevant reviews)
app_stats=[]
for a,g in rel.groupby('app_name'):
    if len(g)>=200:
        app_stats.append({'app':a,'category':g['category'].iloc[0],'n':int(len(g)),
          'neg_pct':round(100*g['neg'].mean(),1),'avg_score':round(g['score'].mean(),2),
          'distress_pct':round(100*g['distress'].mean(),1)})
top_neg_apps = sorted(app_stats,key=lambda x:-x['neg_pct'])[:10]

# timeline (monthly relevant volume + pinjol share)
tl2 = rel.groupby('year_month').size().reset_index(name='total')
tl2 = tl2[tl2['year_month']>='2023-01'].sort_values('year_month')
pin = rel[rel['category']=='pinjol'].groupby('year_month').size()
tl_labels = tl2['year_month'].tolist()
tl_total = tl2['total'].tolist()
tl_pinjol = [int(pin.get(m,0)) for m in tl_labels]
distress_tl = rel.groupby('year_month')['distress'].sum()
tl_distress = [int(distress_tl.get(m,0)) for m in tl_labels]

meta = {'total_reviews':int(nrows_all),'total_relevant':int(len(rel)),'n_apps':int(rel['app_name'].nunique()),
  'n_categories':int(rel['category'].nunique()),'date_min':str(rel['date'].min()),'date_max':str(rel['date'].max()),
  'n_news':int(len(fnews)),'n_forum':int(len(fforum)),'distress_total':int(rel['distress'].sum()),
  'distress_pct':round(100*rel['distress'].mean(),1)}

model = {'algo':'Multinomial Naive Bayes (from scratch)','task':'Klasifikasi Sentimen (Negatif vs Positif)',
  'vocab':int(V),'n_train':int(len(train)),'n_test':int(len(test)),
  'accuracy':round(acc,3),'precision':round(prec,3),'recall':round(rec,3),'f1':round(f1,3),
  'confusion':{'TP':TP,'TN':TN,'FP':FP,'FN':FN},
  'top_neg_words':[w for w,_ in top_neg],'top_pos_words':[w for w,_ in top_pos]}

DATA = {'meta':meta,'model':model,'score_dist':{str(k):int(v) for k,v in rel['score'].value_counts().sort_index().items()},
  'behavior':behavior,'galbay_keywords':kw_counts,'cat_stats':cat_stats,'top_neg_apps':top_neg_apps,
  'timeline':{'labels':tl_labels,'total':tl_total,'pinjol':tl_pinjol,'distress':tl_distress},
  'category_counts':[{'category':k,'count':int(v)} for k,v in rel['category'].value_counts().items()]}

with open(OUT+'data.js','w',encoding='utf-8') as f:
    f.write('// Auto-generated from real scraped data\nwindow.GALBAY_DATA = ')
    json.dump(DATA, f, ensure_ascii=False, indent=2)
    f.write(';\n')
print('Wrote data.js')

# ================= 6) PNG VISUALS (post-modelling) =================
# Confusion matrix
fig,ax=plt.subplots(figsize=(4.2,3.6))
cm=np.array([[TN,FP],[FN,TP]])
im=ax.imshow(cm,cmap='PuBuGn')
ax.set_xticks([0,1]);ax.set_xticklabels(['Pred Neg','Pred Pos'])
ax.set_yticks([0,1]);ax.set_yticklabels(['Aktual Neg','Aktual Pos'])
for i in range(2):
    for j in range(2):
        ax.text(j,i,f'{cm[i,j]:,}',ha='center',va='center',color='#07001a',fontweight='bold',fontsize=13)
ax.set_title('Confusion Matrix (Data Uji)')
plt.tight_layout();plt.savefig(ASSETS+'confusion_matrix.png',dpi=130);plt.close()

# Top negative predictive words
fig,ax=plt.subplots(figsize=(5,4))
ws=[w for w,_ in top_neg][::-1]; vs=[v for _,v in top_neg][::-1]
ax.barh(ws,vs,color=RED)
ax.set_title('Kata Paling Menandai Sentimen Negatif')
ax.set_xlabel('Bobot indikator (log-ratio)')
plt.tight_layout();plt.savefig(ASSETS+'top_neg_words.png',dpi=130);plt.close()

# Distress trend
fig,ax=plt.subplots(figsize=(7,3.4))
ax.plot(tl_labels,tl_total,color=PUR,label='Total review relevan')
ax.plot(tl_labels,tl_distress,color=LIME,label='Sinyal distress galbay')
ax.fill_between(range(len(tl_labels)),tl_distress,color=LIME,alpha=0.12)
step=max(1,len(tl_labels)//10)
ax.set_xticks(range(0,len(tl_labels),step));ax.set_xticklabels(tl_labels[::step],rotation=45,ha='right',fontsize=8)
ax.legend(facecolor='#1a004a',edgecolor='#6a0dad',labelcolor='#f0eaff')
ax.set_title('Tren Volume Review & Sinyal Distress Galbay')
plt.tight_layout();plt.savefig(ASSETS+'distress_trend.png',dpi=130);plt.close()

print('Wrote PNG assets')
print(json.dumps(meta,indent=2,ensure_ascii=False))
print('Behavior:',behavior)
print('KW:',kw_counts[:5])
print('Top neg apps:',[ (a['app'],a['neg_pct']) for a in top_neg_apps[:5]])
