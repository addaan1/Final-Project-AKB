"""Paket processing: transformasi data mentah ke format siap analisis.

Modul:
- build_csv       : ubah JSON raw review menjadi 7 CSV terpisah.
- validate        : deduplication & validation per source.
- sentiment       : VADER sentiment analysis (NLTK), extended for Indonesian.
- id_lexicon      : Indonesian sentiment lexicon/negators/boosters for VADER.
- preprocess      : NLP preprocessing (cleaning, slang normalization).
- visualize       : matplotlib/seaborn charts.
- export_sqlite   : export ke SQLite database.
"""
