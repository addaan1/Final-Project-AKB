"""Scraper komentar TikTok #galbay #paylater #pinjol (PRIORITAS 2).

Menggunakan TikTokApi (unofficial). Fokus Gen Z audience.
Target: video dengan hashtag relevan → ambil komentar.

Etika:
- Tidak simpan username asli (redact ke user_id_hash).
- Simpan teks komentar + timestamp + video metadata.
- Handle rate-limit & anti-bot dengan sleep + retry.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.tiktok")

HASHTAGS: list[str] = [
    "galbay", "gagalbayar", "paylater", "pinjol", "pinjollegal",
    "ditagih", "utang", "cicilan", "gagalbayar", "pinjamanonline",
    "selfreward", "fomo", "checkout", "bayarnanti",
]

MAX_VIDEOS_PER_HASHTAG = 20
MAX_COMMENTS_PER_VIDEO = 50


class TikTokScraper(BaseScraper):
    name = "tiktok"

    @staticmethod
    def _redact_username(username: str) -> str:
        """Redact username menjadi hash untuk privasi."""
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    async def _fetch_hashtag_videos(self, hashtag: str, count: int = MAX_VIDEOS_PER_HASHTAG) -> list[dict]:
        """Ambil list video untuk satu hashtag."""
        from TikTokApi import TikTokApi
        videos = []
        async with TikTokApi() as api:
            await api.create_sessions(
                num_sessions=1,
                sleep_after=3,
                headless=False,
                ms_tokens=[""],
            )
            tag = api.hashtag(name=hashtag)
            async for video in tag.videos(count=count):
                try:
                    info = video.as_dict
                    videos.append({
                        "video_id": info.get("id"),
                        "desc": info.get("desc", ""),
                        "author_id": self._redact_username(info.get("author", {}).get("uniqueId", "")),
                        "create_time": info.get("createTime"),
                        "stats": info.get("stats", {}),
                        "music": info.get("music", {}).get("title", ""),
                    })
                except Exception as e:
                    log.warning("Error parse video %s: %s", hashtag, e)
                self.polite_sleep()
        return videos

    async def _fetch_video_comments(self, video_id: str, count: int = MAX_COMMENTS_PER_VIDEO) -> list[dict]:
        """Ambil komentar untuk satu video."""
        from TikTokApi import TikTokApi
        comments = []
        try:
            async with TikTokApi() as api:
                await api.create_sessions(num_sessions=1, sleep_after=2, headless=False)
                video = api.video(id=video_id)
                async for comment in video.comments(count=count):
                    try:
                        c = comment.as_dict
                        comments.append({
                            "comment_id": c.get("cid"),
                            "video_id": video_id,
                            "text": c.get("text", ""),
                            "user_id": self._redact_username(c.get("user", {}).get("unique_id", "")),
                            "create_time": c.get("create_time"),
                            "likes": c.get("digg_count", 0),
                            "reply_count": c.get("reply_comment_total", 0),
                        })
                    except Exception as e:
                        log.warning("Error parse comment: %s", e)
                    self.polite_sleep()
        except Exception as e:
            log.warning("Gagal fetch comments video %s: %s", video_id, e)
        return comments

    async def _run_async(self, max_videos: int = MAX_VIDEOS_PER_HASHTAG,
                         max_comments: int = MAX_COMMENTS_PER_VIDEO) -> dict[str, Any]:
        """Async runner utama."""
        all_videos = []
        all_comments = []
        per_hashtag = []

        for ht in tqdm(HASHTAGS, desc="Fetch TikTok hashtags"):
            log.info("Scraping hashtag: #%s", ht)
            try:
                videos = await self._fetch_hashtag_videos(ht, count=max_videos)
                all_videos.extend(videos)
                per_hashtag.append({"hashtag": ht, "n_videos": len(videos)})

                for v in tqdm(videos, desc=f"  Comments #{ht}", leave=False):
                    vid = v.get("video_id")
                    if not vid:
                        continue
                    comments = await self._fetch_video_comments(vid, count=max_comments)
                    for c in comments:
                        c["hashtag"] = ht
                        c["video_desc"] = v.get("desc", "")
                        c["video_stats"] = v.get("stats", {})
                    all_comments.extend(comments)
                    self.polite_sleep()
            except Exception as e:
                log.warning("Gagal scrape #%s: %s", ht, e)
                per_hashtag.append({"hashtag": ht, "n_videos": 0, "error": str(e)})

        return {
            "videos": all_videos,
            "comments": all_comments,
            "per_hashtag": per_hashtag,
        }

    def run(self, max_videos: int = MAX_VIDEOS_PER_HASHTAG,
            max_comments: int = MAX_COMMENTS_PER_VIDEO) -> dict[str, Any]:
        """Sync wrapper untuk async runner."""
        try:
            result = asyncio.run(self._run_async(max_videos=max_videos, max_comments=max_comments))
        except Exception as e:
            log.error("TikTok scraper gagal total: %s", e)
            return {"status": "error", "error": str(e), "n_videos": 0, "n_comments": 0}

        videos = result["videos"]
        comments = result["comments"]

        meta = self.meta("tiktok", {
            "n_videos": len(videos),
            "n_comments": len(comments),
            "hashtags": HASHTAGS,
            "max_videos_per_hashtag": max_videos,
            "max_comments_per_video": max_comments,
            "per_hashtag": result["per_hashtag"],
        })

        self.save_json({"meta": meta, "videos": videos}, "tiktok_videos.json", subdir="raw")
        self.save_json({"meta": meta, "comments": comments}, "tiktok_comments.json", subdir="raw")

        sample_comments = comments[:500] if len(comments) > 500 else comments
        self.save_json({"meta": meta, "comments": sample_comments}, "tiktok_comments_sample.json", subdir="sample")

        log.info("TikTok: %d videos, %d comments", len(videos), len(comments))
        return {
            "status": "ok",
            "n_videos": len(videos),
            "n_comments": len(comments),
            "hashtags": HASHTAGS,
        }
