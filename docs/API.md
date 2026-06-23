# Galbay Predictor — API Documentation

Dokumentasi API endpoints untuk **Skor Risiko Galbay** dan **Simulasi Cicilan**.

> **Status saat ini:** Logic berbasis **rule-based** (sudah stable). Akan di-swap ke **ML model** saat modeling tim selesai.
>
> **Backward compatibility:** Response format tidak akan berubah saat model di-swap. Hanya `model_version` yang akan update.

---

## Base URL

```
http://127.0.0.1:5000
```

Untuk production, ganti dengan domain/server yang sesuai.

---

## Endpoints Overview

| Endpoint | Method | Fungsi | Auth |
|---|---|---|---|
| `/api/health` | GET | Health check | - |
| `/api/score` | POST | Hitung Skor Risiko Galbay | - |
| `/api/simulate` | POST | Hitung Simulasi Cicilan | - |
| `/api/waitlist` | POST | Daftar waitlist email | - |

---

## 1. Health Check

### Request

```http
GET /api/health
```

### Response 200

```json
{
  "status": "ok",
  "service": "galbay-predictor-api",
  "model_version": "rule-based-v1"
}
```

---

## 2. Skor Risiko Galbay

### Request

```http
POST /api/score
Content-Type: application/json
```

```json
{
  "apps": ["pinjol", "paylater"],
  "utang": "5to20",
  "selfreward": 7,
  "telat": "1",
  "dc": "1",
  "feeling": "2"
}
```

### Field Reference

| Field | Type | Required | Values | Default |
|---|---|---|---|---|
| `apps` | array of string | yes | `pinjol`, `paylater`, `ewallet`, `bank` | `[]` |
| `utang` | string | yes | `0`, `lt5`, `5to20`, `gt20` | `0` |
| `selfreward` | integer | yes | `1`–`10` (frekuensi per bulan) | `3` |
| `telat` | string | yes | `0` (tidak pernah), `1` (1-2x), `2` (sering) | `0` |
| `dc` | string | yes | `0` (tidak), `1` (ya) | `0` |
| `feeling` | string | yes | `0` (tenang), `1` (waspada), `2` (stress) | `0` |

### Risk Weights (rule-based v1)

| Faktor | Nilai | Bobot Risk |
|---|---|---|
| App: pinjol | binary | +20 |
| App: paylater | binary | +10 |
| App: e-wallet | binary | +5 |
| App: bank digital | binary | +3 |
| Utang: tidak ada | - | 0 |
| Utang: <5jt | - | +10 |
| Utang: 5-20jt | - | +20 |
| Utang: >20jt | - | +30 |
| Self reward: 1-3x/bln | - | +5 |
| Self reward: 4-6x/bln | - | +15 |
| Self reward: 7+x/bln | - | +25 |
| Telat: tidak pernah | - | 0 |
| Telat: 1-2x | - | +15 |
| Telat: sering | - | +25 |
| Debt collector: tidak | - | 0 |
| Debt collector: ya | - | +25 |
| Feeling: tenang | - | 0 |
| Feeling: waspada | - | +10 |
| Feeling: stress | - | +15 |

**Total max:** ~135, **di-cap ke 100**.

### Response 200

```json
{
  "score": 100,
  "category": "bahaya",
  "category_label": "BAHAYA",
  "description": "Risiko galbay tinggi. Butuh intervensi dan perubahan perilaku segera.",
  "recommendations": [
    "<strong>Tunda checkout 24 jam.</strong> Gunakan aturan \"tidur dulu sebelum bayar\"...",
    "<strong>Jangan hindari, negosiasikan.</strong> Lihat modul <em>Cara Negosiasi dengan DC</em>...",
    "<strong>Hindari pinjol baru.</strong> Prioritaskan melunasi yang ada..."
  ],
  "model_version": "rule-based-v1",
  "disclaimer": "Demo Prototype — Skor berbasis rule-based dari insight data 349K ulasan Google Play. Model ML asli menyusul."
}
```

### Category Thresholds

| Score | Category | Label |
|---|---|---|
| 0–30 | `aman` | AMAN — Keuangan sehat |
| 31–60 | `waspada` | WASPADA — Mulai hati-hati |
| 61–100 | `bahaya` | BAHAYA — Butuh intervensi |

### Form-encoded alternative

```http
POST /api/score
Content-Type: application/x-www-form-urlencoded

apps=pinjol&apps=paylater&utang=5to20&selfreward=7&telat=1&dc=1&feeling=2
```

### Example (cURL)

```bash
curl -X POST http://127.0.0.1:5000/api/score \
  -H "Content-Type: application/json" \
  -d '{"apps":["pinjol","paylater"],"utang":"5to20","selfreward":7,"telat":"1","dc":"1","feeling":"2"}'
```

### Example (JavaScript)

```javascript
const resp = await fetch('/api/score', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    apps: ['pinjol', 'paylater'],
    utang: '5to20',
    selfreward: 7,
    telat: '1',
    dc: '1',
    feeling: '2'
  })
});
const result = await resp.json();
console.log(result.score, result.category);
```

---

## 3. Simulasi Cicilan

### Request

```http
POST /api/simulate
Content-Type: application/json
```

```json
{
  "nominal": 2000000,
  "bunga_pct": 10,
  "tenor": 6,
  "admin": 50000
}
```

### Field Reference

| Field | Type | Required | Range | Default |
|---|---|---|---|---|
| `nominal` | float | yes | ≥ 0 (Rp) | 0 |
| `bunga_pct` | float | yes | 0–100 (% per bulan) | 0 |
| `tenor` | integer | yes | ≥ 1 (bulan) | 1 |
| `admin` | float | yes | ≥ 0 (Rp) | 0 |

### Response 200

```json
{
  "valid": true,
  "nominal": 2000000,
  "bunga_pct": 10,
  "tenor": 6,
  "admin": 50000,
  "cicilan": 541667,
  "total_bunga": 1200000,
  "total_bayar": 3250000,
  "bunga_efektif_tahunan": 120.0,
  "warning": "Bunga efektif 120%/tahun — 10x lipat KTA bank (~12%). Sangat memberatkan. Pertimbangkan opsi lain.",
  "tip": "Bunga >100%/tahun = predatory lending. Coba negosiasi tenor lebih panjang atau cari alternatif KTA bank."
}
```

### Calculation Formula

```
total_bunga      = nominal × (bunga_pct / 100) × tenor
total_bayar      = nominal + total_bunga + admin
cicilan          = total_bayar / tenor
bunga_efektif    = (total_bunga / nominal) × (12 / tenor) × 100
```

### Warning Thresholds

| Bunga Efektif | Status | Pesan |
|---|---|---|
| > 100% | 🔴 Berbahaya | Predatory lending |
| > 36% | 🟡 Hati-hati | Di atas rata-rata KTA bank |
| > 18% | 🟢 Wajar | Dalam batas wajar |
| ≤ 18% | 🟢 Rendah | Bunga rendah |

### Response (invalid)

```json
{
  "valid": false,
  "errors": ["nominal harus >= 0"]
}
```

### Example (cURL)

```bash
curl -X POST http://127.0.0.1:5000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"nominal":2000000,"bunga_pct":10,"tenor":6,"admin":50000}'
```

---

## 4. Waitlist

### Request

```http
POST /api/waitlist
Content-Type: application/json
```

```json
{
  "email": "user@example.com",
  "package": "premium"
}
```

### Field Reference

| Field | Type | Required | Default |
|---|---|---|---|
| `email` | string | yes | - |
| `package` | string | no | `general` |

### Response 200

```json
{
  "valid": true,
  "duplicate": false,
  "total": 1
}
```

### Behavior

- Email disimpan ke `data/waitlist.json`
- Cegah duplikat (cek existing email)
- `total` = jumlah entry di waitlist

### Example (cURL)

```bash
curl -X POST http://127.0.0.1:5000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","package":"premium"}'
```

---

## 5. Migration Path ke ML Model

Saat modeling tim selesai, cukup:

### Step 1: Buat function ML

Di `app/api.py`, tambahkan:

```python
def calculate_score_ml(inputs: dict) -> dict:
    """Hitung skor dengan ML model (ganti logic di calculate_score)."""
    # Load model
    import joblib
    model = joblib.load("models/galbay_classifier.pkl")
    
    # Feature engineering
    features = extract_features(inputs)
    
    # Predict
    risk_score = model.predict_proba([features])[0][1] * 100
    score = round(risk_score)
    
    # Map ke category & recommendations (sama seperti rule-based)
    category = "aman" if score <= 30 else ("waspada" if score <= 60 else "bahaya")
    recommendations = generate_recommendations(inputs, score)
    
    return {
        "score": score,
        "category": category,
        "category_label": CATEGORY_LABELS[category]["name"],
        "description": CATEGORY_LABELS[category]["desc"],
        "recommendations": recommendations,
        "model_version": "ml-v1",
        "disclaimer": "Skor berdasarkan model ML yang dilatih dari 349K ulasan Google Play.",
    }
```

### Step 2: Ganti pemanggilan

```python
# Di calculate_score():
def calculate_score(inputs: dict) -> dict:
    try:
        return calculate_score_ml(inputs)
    except Exception:
        return calculate_score_rule_based(inputs)  # fallback
```

### Step 3: Update version

```python
MODEL_VERSION = "ml-v1"  # atau "hybrid-v1", dll
```

### Step 4: Response format TIDAK berubah

Front-end `produk.js` sudah handle response format. Tidak perlu ubah JS.

---

## Error Codes

| Code | Arti |
|---|---|
| 200 | Sukses |
| 400 | Input tidak valid |
| 405 | Method tidak diizinkan (pakai GET untuk endpoint POST, dll) |
| 500 | Server error |

---

## Testing

Jalankan semua test:

```bash
python -m pytest -q
```

Cek coverage:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

---

## File terkait

- `app/api.py` — logic scoring & simulasi
- `app/main.py` — Flask routes
- `app/static/js/produk.js` — front-end (panggil API)
- `tests/test_api.py` — unit tests
- `data/waitlist.json` — hasil dari `/api/waitlist` (auto-generated)
