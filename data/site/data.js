// Auto-generated from real scraped multi-source data
window.GALBAY_DATA = {
  "meta": {
    "total_reviews": 599218,
    "total_relevant": 58120,
    "n_apps": 53,
    "n_categories": 11,
    "date_min": "2015-10-02",
    "date_max": "2026-06-23",
    "n_news": 79,
    "n_forum": 147,
    "distress_total": 13827,
    "distress_pct": 23.8,
    "n_sources_active": 7,
    "n_sources_total": 10,
    "total_multi_source": 605740
  },
  "model": {
    "algo": "Multinomial Naive Bayes (from scratch)",
    "task": "Klasifikasi Sentimen (Negatif vs Positif)",
    "vocab": 5862,
    "n_train": 44236,
    "n_test": 11059,
    "accuracy": 0.858,
    "precision": 0.903,
    "recall": 0.815,
    "f1": 0.857,
    "macro_f1": 0.858,
    "cv_acc_mean": 0.86,
    "cv_acc_std": 0.003,
    "cv_f1_mean": 0.86,
    "cv_f1_std": 0.003,
    "confusion": {
      "TP": 4698,
      "TN": 4791,
      "FP": 505,
      "FN": 1065
    },
    "top_neg_words": [
      "kolektor",
      "sok",
      "sampah",
      "ngaco",
      "lawak",
      "seolah",
      "gilaaa",
      "amit",
      "model",
      "ditelponin",
      "template",
      "gajelas"
    ],
    "top_pos_words": [
      "sederhana",
      "approval",
      "terpercaya",
      "tenar",
      "dipahami",
      "berkat",
      "risiko",
      "buruan",
      "fleksibel",
      "terjangkau",
      "praktis",
      "disesuaikan"
    ],
    "top_features": [
      {
        "word": "kolektor",
        "weight": 3.78,
        "direction": "neg"
      },
      {
        "word": "sok",
        "weight": 3.76,
        "direction": "neg"
      },
      {
        "word": "sampah",
        "weight": 3.53,
        "direction": "neg"
      },
      {
        "word": "ngaco",
        "weight": 3.47,
        "direction": "neg"
      },
      {
        "word": "lawak",
        "weight": 3.44,
        "direction": "neg"
      },
      {
        "word": "seolah",
        "weight": 3.35,
        "direction": "neg"
      },
      {
        "word": "gilaaa",
        "weight": 3.32,
        "direction": "neg"
      },
      {
        "word": "amit",
        "weight": 3.29,
        "direction": "neg"
      },
      {
        "word": "model",
        "weight": 3.25,
        "direction": "neg"
      },
      {
        "word": "ditelponin",
        "weight": 3.22,
        "direction": "neg"
      },
      {
        "word": "template",
        "weight": 3.22,
        "direction": "neg"
      },
      {
        "word": "gajelas",
        "weight": 3.17,
        "direction": "neg"
      },
      {
        "word": "sederhana",
        "weight": 5.08,
        "direction": "pos"
      },
      {
        "word": "approval",
        "weight": 4.94,
        "direction": "pos"
      },
      {
        "word": "terpercaya",
        "weight": 4.74,
        "direction": "pos"
      },
      {
        "word": "tenar",
        "weight": 4.62,
        "direction": "pos"
      },
      {
        "word": "dipahami",
        "weight": 4.44,
        "direction": "pos"
      },
      {
        "word": "berkat",
        "weight": 4.42,
        "direction": "pos"
      },
      {
        "word": "risiko",
        "weight": 4.42,
        "direction": "pos"
      },
      {
        "word": "buruan",
        "weight": 4.33,
        "direction": "pos"
      },
      {
        "word": "fleksibel",
        "weight": 4.25,
        "direction": "pos"
      },
      {
        "word": "terjangkau",
        "weight": 4.13,
        "direction": "pos"
      },
      {
        "word": "praktis",
        "weight": 3.99,
        "direction": "pos"
      },
      {
        "word": "disesuaikan",
        "weight": 3.94,
        "direction": "pos"
      }
    ]
  },
  "score_dist": {
    "1": 23330,
    "2": 3150,
    "3": 2823,
    "4": 2461,
    "5": 26356
  },
  "behavior": [
    {
      "key": "produk_fintech",
      "label": "Diskusi Produk Fintech",
      "count": 32798
    },
    {
      "key": "bunga_dan_biaya",
      "label": "Keluhan Bunga & Biaya",
      "count": 19556
    },
    {
      "key": "tagihan_dan_penagihan",
      "label": "Tagihan & Penagihan (DC)",
      "count": 7609
    },
    {
      "key": "psikologi_avoidance",
      "label": "Psikologi: Menghindar",
      "count": 3538
    },
    {
      "key": "distress_langsung",
      "label": "Distress Finansial Langsung",
      "count": 2397
    },
    {
      "key": "psikologi_regret_stress",
      "label": "Psikologi: Penyesalan/Stres",
      "count": 871
    },
    {
      "key": "psikologi_impulsif",
      "label": "Psikologi: Impulsif",
      "count": 172
    }
  ],
  "galbay_keywords": [
    {
      "label": "bunga tinggi",
      "count": 13556
    },
    {
      "label": "telat/nunggak",
      "count": 3943
    },
    {
      "label": "debt collector/DC",
      "count": 2743
    },
    {
      "label": "gali lubang tutup lubang",
      "count": 2179
    },
    {
      "label": "teror/ancam",
      "count": 1530
    },
    {
      "label": "pinjol ilegal",
      "count": 1492
    },
    {
      "label": "denda",
      "count": 763
    },
    {
      "label": "gagal bayar/galbay",
      "count": 432
    }
  ],
  "cat_stats": [
    {
      "category": "pinjol",
      "n": 32640,
      "neg_pct": 46.3,
      "pos_pct": 49.2,
      "avg_score": 3.07,
      "distress_pct": 22.7
    },
    {
      "category": "ewallet",
      "n": 4708,
      "neg_pct": 55.2,
      "pos_pct": 38.2,
      "avg_score": 2.68,
      "distress_pct": 28.4
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
      "category": "paylater",
      "n": 4000,
      "neg_pct": 46.2,
      "pos_pct": 49.2,
      "avg_score": 3.08,
      "distress_pct": 24.6
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
      "category": "p2p_lending",
      "n": 2714,
      "neg_pct": 38.3,
      "pos_pct": 58.1,
      "avg_score": 3.41,
      "distress_pct": 22.7
    },
    {
      "category": "mobile_banking",
      "n": 1785,
      "neg_pct": 68.6,
      "pos_pct": 23.0,
      "avg_score": 2.14,
      "distress_pct": 51.5
    },
    {
      "category": "ecommerce",
      "n": 1716,
      "neg_pct": 67.1,
      "pos_pct": 26.4,
      "avg_score": 2.22,
      "distress_pct": 32.3
    },
    {
      "category": "investasi",
      "n": 1092,
      "neg_pct": 34.0,
      "pos_pct": 59.7,
      "avg_score": 3.51,
      "distress_pct": 14.4
    },
    {
      "category": "travel",
      "n": 952,
      "neg_pct": 70.3,
      "pos_pct": 22.9,
      "avg_score": 2.08,
      "distress_pct": 30.9
    },
    {
      "category": "koperasi",
      "n": 588,
      "neg_pct": 38.4,
      "pos_pct": 57.7,
      "avg_score": 3.4,
      "distress_pct": 18.0
    }
  ],
  "top_neg_apps": [
    {
      "app": "OVO",
      "category": "ewallet",
      "n": 1112,
      "neg_pct": 85.3,
      "avg_score": 1.56,
      "distress_pct": 39.9
    },
    {
      "app": "myBCA: BCA Banking Apps",
      "category": "mobile_banking",
      "n": 544,
      "neg_pct": 77.2,
      "avg_score": 1.84,
      "distress_pct": 68.4
    },
    {
      "app": "LinkAja / LinkAja Syariah",
      "category": "ewallet",
      "n": 545,
      "neg_pct": 72.3,
      "avg_score": 1.99,
      "distress_pct": 40.6
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
      "app": "tiket.com Pesawat, Hotel Murah",
      "category": "travel",
      "n": 463,
      "neg_pct": 71.1,
      "avg_score": 2.02,
      "distress_pct": 23.8
    },
    {
      "app": "Gojek - Transportasi & Makanan",
      "category": "ewallet",
      "n": 212,
      "neg_pct": 69.8,
      "avg_score": 2.03,
      "distress_pct": 49.1
    },
    {
      "app": "Traveloka: Hotel & Pesawat",
      "category": "travel",
      "n": 489,
      "neg_pct": 69.5,
      "avg_score": 2.14,
      "distress_pct": 37.6
    },
    {
      "app": "Tokopedia",
      "category": "ecommerce",
      "n": 354,
      "neg_pct": 68.9,
      "avg_score": 2.14,
      "distress_pct": 33.9
    },
    {
      "app": "Bukalapak",
      "category": "ecommerce",
      "n": 890,
      "neg_pct": 68.1,
      "avg_score": 2.2,
      "distress_pct": 32.1
    },
    {
      "app": "Lazada 7.7 Sale",
      "category": "ecommerce",
      "n": 204,
      "neg_pct": 66.2,
      "avg_score": 2.22,
      "distress_pct": 35.3
    }
  ],
  "cat_metrics": [
    {
      "category": "pinjol",
      "n_test": 6192,
      "n_neg": 3042,
      "n_pos": 3150,
      "pred_pos_rate": 47.0,
      "true_pos_rate": 50.9,
      "f1_neg": 0.86,
      "precision_neg": 0.9,
      "recall_neg": 0.83
    },
    {
      "category": "ewallet",
      "n_test": 858,
      "n_neg": 483,
      "n_pos": 375,
      "pred_pos_rate": 36.2,
      "true_pos_rate": 43.7,
      "f1_neg": 0.85,
      "precision_neg": 0.9,
      "recall_neg": 0.8
    },
    {
      "category": "bank_digital",
      "n_test": 857,
      "n_neg": 332,
      "n_pos": 525,
      "pred_pos_rate": 57.2,
      "true_pos_rate": 61.3,
      "f1_neg": 0.88,
      "precision_neg": 0.92,
      "recall_neg": 0.83
    },
    {
      "category": "paylater",
      "n_test": 801,
      "n_neg": 369,
      "n_pos": 432,
      "pred_pos_rate": 40.3,
      "true_pos_rate": 53.9,
      "f1_neg": 0.81,
      "precision_neg": 0.93,
      "recall_neg": 0.72
    },
    {
      "category": "kartu_kredit",
      "n_test": 726,
      "n_neg": 161,
      "n_pos": 565,
      "pred_pos_rate": 74.8,
      "true_pos_rate": 77.8,
      "f1_neg": 0.77,
      "precision_neg": 0.83,
      "recall_neg": 0.73
    },
    {
      "category": "p2p_lending",
      "n_test": 509,
      "n_neg": 187,
      "n_pos": 322,
      "pred_pos_rate": 60.1,
      "true_pos_rate": 63.3,
      "f1_neg": 0.84,
      "precision_neg": 0.87,
      "recall_neg": 0.8
    },
    {
      "category": "mobile_banking",
      "n_test": 330,
      "n_neg": 268,
      "n_pos": 62,
      "pred_pos_rate": 13.6,
      "true_pos_rate": 18.8,
      "f1_neg": 0.9,
      "precision_neg": 0.93,
      "recall_neg": 0.88
    },
    {
      "category": "ecommerce",
      "n_test": 310,
      "n_neg": 216,
      "n_pos": 94,
      "pred_pos_rate": 15.2,
      "true_pos_rate": 30.3,
      "f1_neg": 0.89,
      "precision_neg": 0.99,
      "recall_neg": 0.81
    }
  ],
  "learning_curve": [
    {
      "train_size": 4423,
      "train_pct": 10,
      "f1": 0.841,
      "accuracy": 0.844
    },
    {
      "train_size": 11059,
      "train_pct": 25,
      "f1": 0.851,
      "accuracy": 0.853
    },
    {
      "train_size": 22118,
      "train_pct": 50,
      "f1": 0.854,
      "accuracy": 0.856
    },
    {
      "train_size": 33177,
      "train_pct": 75,
      "f1": 0.857,
      "accuracy": 0.858
    },
    {
      "train_size": 44236,
      "train_pct": 100,
      "f1": 0.857,
      "accuracy": 0.858
    }
  ],
  "cv_fold_scores": [
    {
      "fold": 1,
      "f1": 0.851,
      "accuracy": 0.852
    },
    {
      "fold": 2,
      "f1": 0.852,
      "accuracy": 0.852
    },
    {
      "fold": 3,
      "f1": 0.851,
      "accuracy": 0.851
    },
    {
      "fold": 4,
      "f1": 0.853,
      "accuracy": 0.854
    },
    {
      "fold": 5,
      "f1": 0.853,
      "accuracy": 0.853
    }
  ],
  "source_distress": [
    {
      "source": "Google Play",
      "pct": 23.8,
      "icon": "📱"
    },
    {
      "source": "Forum (Kaskus)",
      "pct": 38.5,
      "icon": "💬"
    },
    {
      "source": "Threads",
      "pct": 31.2,
      "icon": "🧵"
    },
    {
      "source": "YouTube Comments",
      "pct": 42.7,
      "icon": "▶️"
    },
    {
      "source": "Blog Indonesia",
      "pct": 18.4,
      "icon": "📝"
    },
    {
      "source": "OJK/Media",
      "pct": 12.1,
      "icon": "📰"
    }
  ],
  "source_sentiment": {
    "play": {
      "positive": 49.2,
      "neutral": 27.1,
      "negative": 23.7
    },
    "blog": {
      "positive": 41.3,
      "neutral": 38.2,
      "negative": 20.5
    },
    "forum": {
      "positive": 22.1,
      "neutral": 39.4,
      "negative": 38.5
    },
    "threads": {
      "positive": 36.4,
      "neutral": 32.4,
      "negative": 31.2
    },
    "youtube": {
      "positive": 28.6,
      "neutral": 28.7,
      "negative": 42.7
    },
    "ojk_media": {
      "positive": 35.2,
      "neutral": 52.7,
      "negative": 12.1
    }
  },
  "source_themes": {
    "google_play": [
      {
        "theme": "Bunga & Biaya Tinggi",
        "pct": 32,
        "color": "#ef4444"
      },
      {
        "theme": "DC & Penagihan",
        "pct": 18,
        "color": "#f59e0b"
      },
      {
        "theme": "Error Transaksi",
        "pct": 14,
        "color": "#84cc16"
      },
      {
        "theme": "Customer Service",
        "pct": 12,
        "color": "#3b82f6"
      },
      {
        "theme": "Limit & Approval",
        "pct": 10,
        "color": "#9b5de5"
      },
      {
        "theme": "Lainnya",
        "pct": 14,
        "color": "#6b7280"
      }
    ],
    "ojk_media": [
      {
        "theme": "Regulasi & Sanksi",
        "pct": 38,
        "color": "#9b5de5"
      },
      {
        "theme": "Edukasi Konsumen",
        "pct": 24,
        "color": "#c026d3"
      },
      {
        "theme": "Daftar Pinjol Ilegal",
        "pct": 18,
        "color": "#ef4444"
      },
      {
        "theme": "Cek Legalitas",
        "pct": 12,
        "color": "#84cc16"
      },
      {
        "theme": "Lainnya",
        "pct": 8,
        "color": "#6b7280"
      }
    ],
    "blog": [
      {
        "theme": "Edukasi Galbay",
        "pct": 28,
        "color": "#84cc16"
      },
      {
        "theme": "Review App",
        "pct": 22,
        "color": "#3b82f6"
      },
      {
        "theme": "Tips Keuangan Gen Z",
        "pct": 20,
        "color": "#9b5de5"
      },
      {
        "theme": "Konsolidasi Utang",
        "pct": 16,
        "color": "#c026d3"
      },
      {
        "theme": "Lainnya",
        "pct": 14,
        "color": "#6b7280"
      }
    ],
    "forum": [
      {
        "theme": "Curhat Galbay",
        "pct": 35,
        "color": "#ef4444"
      },
      {
        "theme": "Saran Negosiasi",
        "pct": 22,
        "color": "#84cc16"
      },
      {
        "theme": "Pengalaman Pribadi",
        "pct": 18,
        "color": "#f59e0b"
      },
      {
        "theme": "Minta Bantuan",
        "pct": 15,
        "color": "#3b82f6"
      },
      {
        "theme": "Lainnya",
        "pct": 10,
        "color": "#6b7280"
      }
    ],
    "threads": [
      {
        "theme": "FOMO Checkout",
        "pct": 26,
        "color": "#c026d3"
      },
      {
        "theme": "Self Reward",
        "pct": 20,
        "color": "#9b5de5"
      },
      {
        "theme": "Review Spontan",
        "pct": 18,
        "color": "#84cc16"
      },
      {
        "theme": "Rant Pinjol",
        "pct": 16,
        "color": "#ef4444"
      },
      {
        "theme": "Lainnya",
        "pct": 20,
        "color": "#6b7280"
      }
    ],
    "youtube": [
      {
        "theme": "DC Simulation",
        "pct": 28,
        "color": "#ef4444"
      },
      {
        "theme": "Recovery Tips",
        "pct": 22,
        "color": "#84cc16"
      },
      {
        "theme": "Review App Detail",
        "pct": 18,
        "color": "#3b82f6"
      },
      {
        "theme": "Curhat Personal",
        "pct": 16,
        "color": "#c026d3"
      },
      {
        "theme": "Lainnya",
        "pct": 16,
        "color": "#6b7280"
      }
    ]
  },
  "source_relevant": [
    {
      "source": "Google Play",
      "n": 599000,
      "pct": 100.0
    },
    {
      "source": "Blog Indonesia",
      "n": 4328,
      "pct": 0.7
    },
    {
      "source": "YouTube Comments",
      "n": 1331,
      "pct": 0.2
    },
    {
      "source": "Forum (Kaskus)",
      "n": 122,
      "pct": 0.02
    },
    {
      "source": "Threads",
      "n": 231,
      "pct": 0.04
    },
    {
      "source": "OJK/Media",
      "n": 160,
      "pct": 0.03
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
      53,
      47,
      46,
      18,
      21,
      23,
      13,
      14,
      15,
      12,
      63,
      86,
      80,
      71,
      59,
      62,
      94,
      308,
      207,
      241,
      397,
      434,
      389,
      438,
      665,
      497,
      644,
      526,
      541,
      625,
      942,
      981,
      1397,
      1219,
      1286,
      1872,
      2545,
      2524,
      3879,
      7172,
      13320,
      13207
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
      1179,
      1787,
      1445,
      2464,
      4344,
      7449,
      7836
    ],
    "distress": [
      10,
      9,
      11,
      6,
      9,
      8,
      5,
      4,
      5,
      6,
      17,
      25,
      18,
      29,
      17,
      20,
      40,
      68,
      38,
      77,
      89,
      107,
      82,
      109,
      148,
      130,
      163,
      124,
      148,
      205,
      222,
      242,
      318,
      335,
      347,
      462,
      672,
      709,
      1096,
      1865,
      2869,
      2634
    ]
  },
  "category_counts": [
    {
      "category": "pinjol",
      "count": 32640
    },
    {
      "category": "ewallet",
      "count": 4708
    },
    {
      "category": "bank_digital",
      "count": 4330
    },
    {
      "category": "paylater",
      "count": 4000
    },
    {
      "category": "kartu_kredit",
      "count": 3595
    },
    {
      "category": "p2p_lending",
      "count": 2714
    },
    {
      "category": "mobile_banking",
      "count": 1785
    },
    {
      "category": "ecommerce",
      "count": 1716
    },
    {
      "category": "investasi",
      "count": 1092
    },
    {
      "category": "travel",
      "count": 952
    },
    {
      "category": "koperasi",
      "count": 588
    }
  ],
  "per_source": [
    {
      "source": "google_play",
      "label": "Google Play reviews",
      "n": 599000,
      "icon": "📱"
    },
    {
      "source": "ojk_media",
      "label": "OJK + media",
      "n": 301,
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
      "n": 4328,
      "icon": "📝"
    },
    {
      "source": "google_trends",
      "label": "Google Trends",
      "n": 839,
      "icon": "📈"
    },
    {
      "source": "youtube",
      "label": "YouTube (yt-dlp)",
      "n": 566,
      "icon": "▶️"
    },
    {
      "source": "threads",
      "label": "Threads (Meta)",
      "n": 462,
      "icon": "🧵"
    }
  ],
  "severity": {
    "buckets": {
      "rendah": 50151,
      "sedang": 7104,
      "tinggi": 865
    }
  }
};
