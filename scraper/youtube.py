"""Scraper YouTube comments (PRIORITAS 9 - baru, butuh API key gratis).

Menggunakan YouTube Data API v3. Free tier: 10,000 quota units/day.

Cara dapat API key:
1. Buka https://console.cloud.google.com
2. Buat project baru
3. Enable "YouTube Data API v3"
4. Credentials > Create API Key
5. Copy key ke .env: YOUTUBE_API_KEY=...
"""
from __future__ import annotations

import logging
import time
from typing import Any

from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.youtube")

SEARCH_QUERIES: list[str] = [
    "galbay paylater", "gagal bayar pinjol", "tips paylater",
    "bahaya pinjol", "review kredivo", "review akulaku",
    "cicilan paylater", "self reward gen z", "fomo belanja",
]

MAX_VIDEOS_PER_QUERY = 10
MAX_COMMENTS_PER_VIDEO = 50


class YouTubeScraper(BaseScraper):
    name = "youtube"

    def __init__(self, sleep_seconds: float = 0.0):
        super().__init__(sleep_seconds)
        self.api_key = self.get_env("YOUTUBE_API_KEY", "")
        if not self.api_key:
            log.warning("YOUTUBE_API_KEY belum diset di .env. YouTube scraper tidak bisa jalan.")

    def _search_videos(self, query: str, max_videos: int) -> list[dict]:
        import requests
        if not self.api_key:
            return []
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet", "q": query, "type": "video",
            "maxResults": max_videos, "order": "relevance",
            "regionCode": "ID", "relevanceLanguage": "id",
            "key": self.api_key,
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                log.warning("YouTube search '%s' status %d", query, r.status_code)
                return []
            data = r.json()
            videos = []
            for item in data.get("items", []):
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                })
            return videos
        except Exception as e:
            log.warning("YouTube search error: %s", e)
            return []

    def _get_comments(self, video_id: str, max_comments: int) -> list[dict]:
        import requests
        if not self.api_key:
            return []
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet", "videoId": video_id,
            "maxResults": min(max_comments, 100), "order": "relevance",
            "textFormat": "plainText", "key": self.api_key,
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                return []
            data = r.json()
            comments = []
            for item in data.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "video_id": video_id,
                    "comment_id": item["id"],
                    "text": snippet.get("textDisplay", ""),
                    "author": snippet.get("authorDisplayName", ""),
                    "likes": snippet.get("likeCount", 0),
                    "published_at": snippet.get("publishedAt"),
                })
            return comments
        except Exception as e:
            log.warning("YouTube comments error: %s", e)
            return []

    def run(self, max_videos: int = MAX_VIDEOS_PER_QUERY, max_comments: int = MAX_COMMENTS_PER_VIDEO) -> dict[str, Any]:
        if not self.api_key:
            return {"status": "no_api_key", "n_comments": 0}
        all_comments = []
        per_query = []
        for query in tqdm(SEARCH_QUERIES, desc="YouTube queries"):
            videos = self._search_videos(query, max_videos)
            log.info("YouTube '%s': %d videos", query, len(videos))
            for v in videos:
                comments = self._get_comments(v["video_id"], max_comments)
                for c in comments:
                    c["query"] = query
                    c["video_title"] = v["title"]
                    c["channel"] = v["channel"]
                all_comments.extend(comments)
                self.polite_sleep()
            per_query.append({"query": query, "n_videos": len(videos)})
        meta = self.meta("youtube", {
            "n_comments": len(all_comments), "queries": SEARCH_QUERIES,
            "per_query": per_query,
        })
        self.save_json({"meta": meta, "comments": all_comments}, "youtube_comments.json", subdir="raw")
        sample = all_comments[:500] if len(all_comments) > 500 else all_comments
        self.save_json({"meta": meta, "comments": sample}, "youtube_comments_sample.json", subdir="sample")
        return {
            "status": "ok" if all_comments else "no_data",
            "n_comments": len(all_comments), "queries": SEARCH_QUERIES,
        }
