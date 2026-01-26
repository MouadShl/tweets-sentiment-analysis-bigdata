from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable

import requests


@dataclass(frozen=True)
class RedditClient:
    user_agent: str
    timeout_seconds: float = 15.0

    def __post_init__(self) -> None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }
        )
        object.__setattr__(self, "_session", s)

    def fetch_json(self, url: str) -> Dict[str, Any]:
        r = self._session.get(url, timeout=self.timeout_seconds)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def iter_children(listing: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        data = listing.get("data") or {}
        children = data.get("children") or []
        for child in children:
            if isinstance(child, dict) and "data" in child:
                yield child["data"]

    def fetch_new_posts(self, subreddit: str, limit: int = 100) -> list[Dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        listing = self.fetch_json(url)
        return list(self.iter_children(listing))

    def fetch_new_comments(self, subreddit: str, limit: int = 100) -> list[Dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/comments.json?limit={limit}"
        listing = self.fetch_json(url)
        return list(self.iter_children(listing))

