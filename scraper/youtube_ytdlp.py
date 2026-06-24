"""Scraper YouTube via yt-dlp (no API key, no Playwright).

yt-dlp extract video metadata + comments JSON dari search results. Support
pagination. Lebih reliable dari YouTube Data API (perlu key) atau Playwright
(sering kena deteksi headless).

Output schema per video:
    {
        "source": "youtube",
        "query": str,
        "title": str,
        "channel": str,
        "channel_id": str,
        "video_id": str,
        "url": str,
        "duration": int,         # seconds
        "view_count": int,
        "like_count": int,
        "upload_date": str,      # YYYYMMDD
        "description": str,      # truncated
        "tags": list[str],
        "categories": list[str],
        "scraped_at": float,
    }

Per comment:
    {
        "source": "youtube",
        "query": str,
        "video_id": str,
        "video_title": str,
        "comment_id": str,
        "author": str,
        "text": str,
        "like_count": int,
        "reply_count": int,
        "timestamp": float,
        "scraped_at": float,
    }
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from tqdm import tqdm
from yt_dlp import YoutubeDL

from scraper.base import BaseScraper

log = logging.getLogger("scraper.youtube_ytdlp")

YT_QUERIES: list[str] = [
    "galbay paylater",
    "gagal bayar pinjol",
    "debt collector indonesia",
    "tips bayar paylater",
    "pinjaman online indonesia",
    "cicilan 0 persen",
    "self reward shopee",
    "checkout bayar nanti",
    "FOMO belanja online",
    "kartu kredit indonesia",
    "kredivo review",
    "shopee paylater cicilan",
    "akulaku gagal bayar",
    "indodana review",
    "koinworks review",
    "amartha review",
    "literasi keuangan gen z",
    "tips keuangan gen z",
    "konsolidasi utang",
    "restrukturisasi kredit",
    "kredit pintar review",
    "julo gagal bayar",
    "kredito review",
    "uangme review",
    "tunaiku review",
    "kta kilat",
    "pinjaman online ilegal",
    "pinjol legal OJK",
    "bunga pinjol tinggi",
    "tips keluar dari galbay",
    "cara bayar pinjol",
    "negosiasi debt collector",
    "konsolidasi pinjol",
    "tagihan shopee paylater",
    "tagihan kredivo",
    "tagihan akulaku",
    "bayar paylater telat",
    "denda pinjol",
    "live streaming utang",
    "curhat pinjol",
]


class YoutubeYtdlpScraper(BaseScraper):
    name = "youtube_ytdlp"

    def _extract_videos(self, query: str, max_videos: int = 25) -> list[dict]:
        """Extract video metadata dari search results."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
            "writesubtitles": False,
            "writeautomaticsub": False,
        }
        videos: list[dict] = []
        try:
            with YoutubeDL(ydl_opts) as ydl:
                url = f"ytsearch{max_videos}:{query}"
                r = ydl.extract_info(url, download=False)
                for entry in r.get("entries", []):
                    if not entry:
                        continue
                    videos.append(
                        {
                            "source": "youtube",
                            "query": query,
                            "title": entry.get("title", "")[:200],
                            "channel": entry.get("channel", entry.get("uploader", "")),
                            "channel_id": entry.get("channel_id", ""),
                            "video_id": entry.get("id", ""),
                            "url": entry.get("url", f"https://www.youtube.com/watch?v={entry.get('id', '')}"),
                            "duration": int(entry.get("duration", 0) or 0),
                            "view_count": int(entry.get("view_count", 0) or 0),
                            "like_count": int(entry.get("like_count", 0) or 0),
                            "upload_date": str(entry.get("upload_date", "")),
                            "description": str(entry.get("description", ""))[:1000],
                            "tags": entry.get("tags", [])[:10],
                            "categories": entry.get("categories", []),
                            "scraped_at": time.time(),
                        }
                    )
        except Exception as exc:
            log.warning("yt-dlp search '%s' error: %s", query, exc)
        return videos

    def _extract_comments(self, video: dict, max_comments: int = 30) -> list[dict]:
        """Fetch comments untuk satu video via yt-dlp get_info_comments."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "getcomments": True,
            "extractor_args": {"youtube": {"max_comments": [str(max_comments)]}},
        }
        comments: list[dict] = []
        try:
            with YoutubeDL(ydl_opts) as ydl:
                r = ydl.extract_info(video["url"], download=False)
                if not r:
                    return comments
                for c in r.get("comments", []) or []:
                    comments.append(
                        {
                            "source": "youtube",
                            "query": video["query"],
                            "video_id": video["video_id"],
                            "video_title": video["title"],
                            "comment_id": c.get("id", ""),
                            "author": c.get("author", ""),
                            "text": str(c.get("text", ""))[:1000],
                            "like_count": int(c.get("like_count", 0) or 0),
                            "reply_count": int(c.get("reply_count", 0) or 0),
                            "timestamp": float(c.get("timestamp", 0) or 0),
                            "scraped_at": time.time(),
                        }
                    )
        except Exception as exc:
            # Comments often fail for disabled comments, age-restricted, etc.
            log.debug("yt-dlp comments for '%s' failed: %s", video["title"][:30], exc)
        return comments

    def run(
        self,
        max_videos_per_query: int = 30,
        max_comments_per_video: int = 30,
        fetch_comments: bool = True,
    ) -> dict[str, Any]:
        """Scrape YouTube via yt-dlp."""
        all_videos: list[dict] = []
        all_comments: list[dict] = []
        per_query: list[dict] = []

        for query in tqdm(YT_QUERIES, desc="YouTube queries"):
            try:
                videos = self._extract_videos(query, max_videos=max_videos_per_query)
                all_videos.extend(videos)

                if fetch_comments:
                    for v in videos[:8]:  # top 8 videos for comments (more coverage)
                        c = self._extract_comments(v, max_comments=max_comments_per_video)
                        all_comments.extend(c)

                per_query.append(
                    {
                        "query": query,
                        "n_videos": len(videos),
                        "n_comments": sum(1 for c in all_comments if c.get("query") == query),
                    }
                )
            except Exception as exc:
                log.warning("YouTube q='%s' error: %s", query, exc)
                per_query.append({"query": query, "n_videos": 0, "n_comments": 0, "error": str(exc)})
            time.sleep(1.0)

        # Dedup
        seen = set()
        unique_videos = []
        for v in all_videos:
            if v["video_id"] and v["video_id"] not in seen:
                seen.add(v["video_id"])
                unique_videos.append(v)
        all_videos = unique_videos

        seen_c = set()
        unique_comments = []
        for c in all_comments:
            if c.get("comment_id") and c["comment_id"] not in seen_c:
                seen_c.add(c["comment_id"])
                unique_comments.append(c)
        all_comments = unique_comments

        meta = self.meta(
            "youtube_ytdlp",
            {
                "n_videos": len(all_videos),
                "n_comments": len(all_comments),
                "n_total": len(all_videos) + len(all_comments),
                "queries": YT_QUERIES,
                "max_videos_per_query": max_videos_per_query,
                "max_comments_per_video": max_comments_per_video,
                "per_query": per_query,
            },
        )

        out = {"meta": meta, "videos": all_videos, "comments": all_comments}
        self.save_json(out, "youtube_ytdlp.json", subdir="raw")

        # Sample (videos full + comments top 200)
        sample = {
            "meta": meta,
            "videos": all_videos[:500] if len(all_videos) > 500 else all_videos,
            "comments": all_comments[:300] if len(all_comments) > 300 else all_comments,
        }
        self.save_json(sample, "youtube_ytdlp_sample.json", subdir="sample")

        log.info(
            "YouTube (yt-dlp): %d videos + %d comments dari %d query",
            len(all_videos), len(all_comments), len(YT_QUERIES),
        )
        return {
            "status": "ok" if all_videos else "no_data",
            "n_videos": len(all_videos),
            "n_comments": len(all_comments),
            "n_total": len(all_videos) + len(all_comments),
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    with_comments = "--no-comments" not in sys.argv
    result = YoutubeYtdlpScraper().run(
        max_videos_per_query=n, fetch_comments=with_comments
    )
    print(json.dumps(result, indent=2, default=str))
