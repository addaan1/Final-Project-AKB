// Auto-generated from real scraped multi-source data
window.GALBAY_DATA = {
  "meta": {
    "total_reviews": 349201,
    "total_relevant": 35968,
    "n_apps": 44,
    "n_categories": 11,
    "date_min": "2022-06-10",
    "date_max": "2026-06-21",
    "n_news": 79,
    "n_forum": 147,
    "distress_total": 8340,
    "distress_pct": 23.2,
    "n_sources_active": 5,
    "n_sources_total": 10,
    "total_multi_source": 350123
  },
  "model": {
    "algo": "Multinomial Naive Bayes (from scratch)",
    "task": "Klasifikasi Sentimen (Negatif vs Positif)",
    "vocab": 4446,
    "n_train": 27271,
    "n_test": 6819,
    "accuracy": 0.846,
    "precision": 0.878,
    "recall": 0.807,
    "f1": 0.841,
    "macro_f1": 0.846,
    "cv_acc_mean": 0.848,
    "cv_acc_std": 0.002,
    "cv_f1_mean": 0.848,
    "cv_f1_std": 0.002,
    "confusion": {
      "TP": 2767,
      "TN": 3003,
      "FP": 386,
      "FN": 663
    },
    "top_neg_words": [
      "lintah",
      "darat",
      "gausah",
      "gajelas",
      "tolol",
      "berkedok",
      "sok",
      "sampah",
      "ngomong",
      "boro",
      "bodoh",
      "nyuruh"
    ],
    "top_pos_words": [
      "nyuruh",
      "bodoh",
      "boro",
      "ngomong",
      "sampah",
      "sok",
      "berkedok",
      "tolol",
      "gajelas",
      "gausah",
      "darat",
      "lintah"
    ]
  },
  "score_dist": {
    "1": 14918,
    "2": 2026,
    "3": 1877,
    "4": 1645,
    "5": 15502
  },
  "behavior": [
    {
      "key": "produk_fintech",
      "label": "Diskusi Produk Fintech",
      "count": 20246
    },
    {
      "key": "bunga_dan_biaya",
      "label": "Keluhan Bunga & Biaya",
      "count": 12445
    },
    {
      "key": "tagihan_dan_penagihan",
      "label": "Tagihan & Penagihan (DC)",
      "count": 4809
    },
    {
      "key": "psikologi_avoidance",
      "label": "Psikologi: Menghindar",
      "count": 1976
    },
    {
      "key": "distress_langsung",
      "label": "Distress Finansial Langsung",
      "count": 1442
    },
    {
      "key": "psikologi_regret_stress",
      "label": "Psikologi: Penyesalan/Stres",
      "count": 473
    },
    {
      "key": "psikologi_impulsif",
      "label": "Psikologi: Impulsif",
      "count": 144
    }
  ],
  "galbay_keywords": [
    {
      "label": "bunga tinggi",
      "count": 8567
    },
    {
      "label": "telat/nunggak",
      "count": 2348
    },
    {
      "label": "debt collector/DC",
      "count": 1673
    },
    {
      "label": "gali lubang tutup lubang",
      "count": 1292
    },
    {
      "label": "teror/ancam",
      "count": 972
    },
    {
      "label": "pinjol ilegal",
      "count": 790
    },
    {
      "label": "denda",
      "count": 458
    },
    {
      "label": "gagal bayar/galbay",
      "count": 272
    }
  ],
  "cat_stats": [
    {
      "category": "pinjol",
      "n": 21802,
      "neg_pct": 52.5,
      "pos_pct": 42.1,
      "avg_score": 2.8,
      "distress_pct": 23.7
    },
    {
      "category": "bank_digital",
      "n": 4330,
      "neg_pct": 34.3,
      "pos_pct": 60.9,
      "avg_score": 3.52,
      "distress_pct": 22.2
    },
    {
      "category": "kartu_kredit",
      "n": 3595,
      "neg_pct": 21.1,
      "pos_pct": 75.7,
      "avg_score": 4.09,
      "distress_pct": 13.5
    },
    {
      "category": "ewallet",
      "n": 2658,
      "neg_pct": 44.8,
      "pos_pct": 48.5,
      "avg_score": 3.08,
      "distress_pct": 21.6
    },
    {
      "category": "paylater",
      "n": 1161,
      "neg_pct": 47.1,
      "pos_pct": 48.3,
      "avg_score": 3.05,
      "distress_pct": 23.3
    },
    {
      "category": "mobile_banking",
      "n": 812,
      "neg_pct": 70.4,
      "pos_pct": 20.7,
      "avg_score": 2.07,
      "distress_pct": 47.9
    },
    {
      "category": "koperasi",
      "n": 588,
      "neg_pct": 38.4,
      "pos_pct": 57.7,
      "avg_score": 3.4,
      "distress_pct": 18.0
    },
    {
      "category": "ecommerce",
      "n": 452,
      "neg_pct": 71.9,
      "pos_pct": 23.9,
      "avg_score": 2.07,
      "distress_pct": 35.8
    },
    {
      "category": "travel",
      "n": 260,
      "neg_pct": 67.7,
      "pos_pct": 26.9,
      "avg_score": 2.21,
      "distress_pct": 35.0
    },
    {
      "category": "p2p_lending",
      "n": 255,
      "neg_pct": 78.4,
      "pos_pct": 18.0,
      "avg_score": 1.84,
      "distress_pct": 44.7
    },
    {
      "category": "investasi",
      "n": 55,
      "neg_pct": 32.7,
      "pos_pct": 65.5,
      "avg_score": 3.64,
      "distress_pct": 30.9
    }
  ],
  "top_neg_apps": [
    {
      "app": "OVO",
      "category": "ewallet",
      "n": 366,
      "neg_pct": 85.0,
      "avg_score": 1.58,
      "distress_pct": 40.2
    },
    {
      "app": "KoinWorks Pendanaan Super App",
      "category": "p2p_lending",
      "n": 255,
      "neg_pct": 78.4,
      "avg_score": 1.84,
      "distress_pct": 44.7
    },
    {
      "app": "Livin' by Mandiri",
      "category": "mobile_banking",
      "n": 744,
      "neg_pct": 71.5,
      "avg_score": 2.02,
      "distress_pct": 47.7
    },
    {
      "app": "Home Credit-Pinjaman & Kredit",
      "category": "pinjol",
      "n": 3046,
      "neg_pct": 65.9,
      "avg_score": 2.27,
      "distress_pct": 23.5
    },
    {
      "app": "Indosaku-Pinjaman Cicilan Uang",
      "category": "pinjol",
      "n": 1177,
      "neg_pct": 64.4,
      "avg_score": 2.36,
      "distress_pct": 27.3
    },
    {
      "app": "JULO: Pinjaman & Kredit Online",
      "category": "pinjol",
      "n": 3522,
      "neg_pct": 60.3,
      "avg_score": 2.5,
      "distress_pct": 26.0
    },
    {
      "app": "KrediOne-Pinjaman Daring",
      "category": "pinjol",
      "n": 1367,
      "neg_pct": 56.0,
      "avg_score": 2.6,
      "distress_pct": 20.3
    },
    {
      "app": "Akulaku--Pinjaman Online Cepat",
      "category": "paylater",
      "n": 541,
      "neg_pct": 53.6,
      "avg_score": 2.79,
      "distress_pct": 19.4
    },
    {
      "app": "Cairin: Pinjaman Dana Instan",
      "category": "pinjol",
      "n": 1937,
      "neg_pct": 53.5,
      "avg_score": 2.75,
      "distress_pct": 27.8
    },
    {
      "app": "Indodana: PayLater & Pinjaman",
      "category": "paylater",
      "n": 205,
      "neg_pct": 52.7,
      "avg_score": 2.74,
      "distress_pct": 22.9
    }
  ],
  "timeline": {
    "labels": [
      "2023-01",
      "2023-02",
      "2023-03",
      "2023-04",
      "2023-05",
      "2023-06",
      "2023-07",
      "2023-08",
      "2023-09",
      "2023-10",
      "2023-11",
      "2023-12",
      "2024-01",
      "2024-02",
      "2024-03",
      "2024-04",
      "2024-05",
      "2024-06",
      "2024-07",
      "2024-08",
      "2024-09",
      "2024-10",
      "2024-11",
      "2024-12",
      "2025-01",
      "2025-02",
      "2025-03",
      "2025-04",
      "2025-05",
      "2025-06",
      "2025-07",
      "2025-08",
      "2025-09",
      "2025-10",
      "2025-11",
      "2025-12",
      "2026-01",
      "2026-02",
      "2026-03",
      "2026-04",
      "2026-05",
      "2026-06"
    ],
    "total": [
      11,
      11,
      12,
      10,
      11,
      10,
      7,
      5,
      5,
      5,
      5,
      5,
      3,
      4,
      6,
      4,
      8,
      62,
      86,
      181,
      341,
      377,
      326,
      355,
      624,
      472,
      599,
      477,
      498,
      587,
      902,
      947,
      1265,
      1029,
      1119,
      1536,
      1920,
      1689,
      1842,
      3528,
      6931,
      8006
    ],
    "pinjol": [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      117,
      262,
      286,
      233,
      253,
      499,
      337,
      417,
      312,
      346,
      350,
      481,
      456,
      683,
      535,
      569,
      995,
      1405,
      1109,
      1145,
      2466,
      3945,
      4601
    ],
    "distress": [
      4,
      3,
      5,
      5,
      6,
      3,
      2,
      0,
      2,
      3,
      2,
      5,
      1,
      2,
      4,
      3,
      3,
      10,
      12,
      51,
      71,
      80,
      61,
      88,
      137,
      125,
      152,
      110,
      132,
      190,
      211,
      230,
      280,
      250,
      265,
      327,
      439,
      387,
      467,
      886,
      1605,
      1672
    ]
  },
  "category_counts": [
    {
      "category": "pinjol",
      "count": 21802
    },
    {
      "category": "bank_digital",
      "count": 4330
    },
    {
      "category": "kartu_kredit",
      "count": 3595
    },
    {
      "category": "ewallet",
      "count": 2658
    },
    {
      "category": "paylater",
      "count": 1161
    },
    {
      "category": "mobile_banking",
      "count": 812
    },
    {
      "category": "koperasi",
      "count": 588
    },
    {
      "category": "ecommerce",
      "count": 452
    },
    {
      "category": "travel",
      "count": 260
    },
    {
      "category": "p2p_lending",
      "count": 255
    },
    {
      "category": "investasi",
      "count": 55
    }
  ],
  "per_source": [
    {
      "source": "google_play",
      "label": "Google Play reviews",
      "n": 349200,
      "icon": "📱"
    },
    {
      "source": "ojk_media",
      "label": "OJK + media",
      "n": 582,
      "icon": "📰"
    },
    {
      "source": "forum",
      "label": "Forum (Kaskus + Reddit)",
      "n": 244,
      "icon": "💬"
    },
    {
      "source": "blog",
      "label": "Blog (Medium + Dailysia)",
      "n": 44,
      "icon": "📝"
    },
    {
      "source": "google_trends",
      "label": "Google Trends",
      "n": 53,
      "icon": "📈"
    }
  ],
  "severity": {
    "buckets": {
      "rendah": 31028,
      "sedang": 4436,
      "tinggi": 504
    }
  }
};
