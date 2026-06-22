"""CLI orchestrator untuk menjalankan scraper.

Penggunaan:
    python -m scraper.runner --source play_reviews
<<<<<<< HEAD
    python -m scraper.runner --source play_reviews --mode sample --count 1000
    python -m scraper.runner --source play_reviews --mode all              # big data (semua review)
    python -m scraper.runner --source play_reviews --mode all --max-per-app 5000
=======
>>>>>>> origin/main
    python -m scraper.runner --source google_trends
    python -m scraper.runner --source all
    python -m scraper.runner --list
"""
from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("scraper.runner")


def get_sources():
    """Registry source -> (import callable, deskripsi). Lazy import agar
    stub yang library-nya belum terinstall tidak crash runner."""
    return {
<<<<<<< HEAD
        "play_reviews": ("scraper.fintech_reviews:GooglePlayReviewsScraper", "Google Play reviews app fintech (44 app, 15K cap)"),
        "google_trends": ("scraper.google_trends:GoogleTrendsScraper", "Tren keyword galbay/paylater/pinjol (pytrends)"),
        "appstore": ("scraper.appstore_reviews:AppStoreReviewsScraper", "Apple App Store reviews iOS (15 app)"),
        "tiktok": ("scraper.tiktok:TikTokScraper", "Komentar TikTok #galbay (Playwright)"),
        "twitter": ("scraper.twitter:TwitterScraper", "Post X/Twitter (Playwright, login-wall)"),
        "instagram": ("scraper.instagram:InstagramScraper", "Caption/komentar Instagram (stub)"),
        "forum": ("scraper.forum:ForumScraper", "Kaskus threads + Reddit posts (Playwright)"),
        "ojk_news": ("scraper.ojk_news:OjkNewsScraper", "OJK + 12 media besar (kompas/detik/cnbc/antara/dll)"),
        "blogs": ("scraper.blogs:BlogScraper", "Blog posts (Medium + Dailysia)"),
        "youtube": ("scraper.youtube:YouTubeScraper", "YouTube comments (butuh API key)"),
=======
        "play_reviews": ("scraper.fintech_reviews:GooglePlayReviewsScraper", "Google Play reviews app fintech (PRIORITAS 1, volume tinggi)"),
        "google_trends": ("scraper.google_trends:GoogleTrendsScraper", "Tren keyword galbay/paylater/pinjol"),
        "tiktok": ("scraper.tiktok:TikTokScraper", "Komentar TikTok #galbay #paylater (stub)"),
        "twitter": ("scraper.twitter:TwitterScraper", "Post X/Twitter keyword galbay (stub)"),
        "instagram": ("scraper.instagram:InstagramScraper", "Caption/komentar Instagram (stub)"),
        "forum": ("scraper.forum:ForumScraper", "Kaskus & Reddit thread utang (stub)"),
        "ojk_news": ("scraper.ojk_news:OjkNewsScraper", "Siaran pers & berita OJK (stub)"),
>>>>>>> origin/main
    }


def load_class(path: str):
    module_name, class_name = path.split(":")
    import importlib
    mod = importlib.import_module(module_name)
    return getattr(mod, class_name)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Galbay Predictor scraper runner")
    parser.add_argument("--source", "-s", help="Nama source scraper")
<<<<<<< HEAD
    parser.add_argument("--count", "-n", type=int, default=400, help="Jumlah review/item per app pada mode sample (default 400)")
    parser.add_argument("--apps", type=int, default=0, help="Batasi jumlah app (0 = semua)")
    parser.add_argument("--mode", "-m", choices=["sample", "all"], default="sample",
                        help="mode sample (cepat) atau all (semua review, big data)")
    parser.add_argument("--max-per-app", type=int, default=0,
                        help="Cap review per app pada mode all (0 = unlimited)")
    parser.add_argument("--max-videos", type=int, default=20,
                        help="Max video per hashtag untuk TikTok (default 20)")
    parser.add_argument("--max-comments", type=int, default=50,
                        help="Max komentar per video TikTok (default 50)")
    parser.add_argument("--max-threads", type=int, default=50,
                        help="Max threads per query untuk Kaskus (default 50)")
    parser.add_argument("--max-posts", type=int, default=50,
                        help="Max posts per query untuk Reddit (default 50)")
    parser.add_argument("--max-tweets", type=int, default=50,
                        help="Max tweets per query untuk Twitter/Nitter (default 50)")
    parser.add_argument("--max-articles", type=int, default=30,
                        help="Max articles per query untuk OJK/media (default 30)")
=======
    parser.add_argument("--count", "-n", type=int, default=400, help="Jumlah review/item per app (default 400)")
    parser.add_argument("--apps", type=int, default=0, help="Batasi jumlah app (0 = semua)")
>>>>>>> origin/main
    parser.add_argument("--list", action="store_true", help="Daftar source tersedia")
    parser.add_argument("--all", action="store_true", help="Jalankan semua source")
    args = parser.parse_args(argv)

    sources = get_sources()

    if args.list:
        print("Source tersedia:")
        for k, v in sources.items():
            print(f"  {k:15s} — {v[1]}")
        return 0

    if args.all:
        targets = list(sources.keys())
    elif args.source:
        if args.source not in sources:
            log.error("Source '%s' tidak dikenal. Pakai --list untuk lihat opsi.", args.source)
            return 1
        targets = [args.source]
    else:
        parser.print_help()
        return 1

    summary = {}
    for src in targets:
        path, desc = sources[src]
        log.info("=== Menjalankan %s (%s) ===", src, desc)
        try:
            cls = load_class(path)
            scraper = cls()
            kwargs = {}
            if src == "play_reviews":
                kwargs["count"] = args.count
<<<<<<< HEAD
                kwargs["mode"] = args.mode
                kwargs["max_per_app"] = args.max_per_app
                if args.apps:
                    kwargs["app_limit"] = args.apps
            elif src == "appstore":
                kwargs["count"] = args.count
                if args.apps:
                    kwargs["app_limit"] = args.apps
            elif src == "tiktok":
                kwargs["max_videos"] = args.max_videos
                kwargs["max_comments"] = args.max_comments
            elif src == "forum":
                kwargs["max_threads"] = args.max_threads
                kwargs["max_posts"] = args.max_posts
            elif src == "twitter":
                kwargs["max_tweets"] = args.max_tweets
            elif src == "ojk_news":
                kwargs["max_ojk_articles"] = args.max_articles
                kwargs["max_media_per_query"] = max(5, args.max_articles // 2)
            elif src == "blogs":
                kwargs["max_per_query"] = max(10, args.max_articles)
            elif src == "youtube":
                kwargs["max_videos"] = args.max_videos
                kwargs["max_comments"] = args.max_comments
=======
                if args.apps:
                    kwargs["app_limit"] = args.apps
>>>>>>> origin/main
            result = scraper.run(**kwargs)
            summary[src] = result
            log.info("Selesai %s: %s", src, result)
        except NotImplementedError:
            log.warning("Source '%s' masih stub (NotImplementedError). Skip.", src)
            summary[src] = {"status": "stub"}
        except Exception as e:
            log.exception("Gagal menjalankan %s: %s", src, e)
            summary[src] = {"status": "error", "error": str(e)}

    print("\n=== RINGKASAN ===")
    import json
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
