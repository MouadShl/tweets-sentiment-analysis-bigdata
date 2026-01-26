from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .reddit_client import RedditClient


def _created_utc(d: Dict[str, Any]) -> int:
    return int(d.get("created_utc") or 0)


@dataclass(frozen=True)
class PollResult:
    new_items: List[Dict[str, Any]]
    new_high_watermark: int


def poll_posts(
    client: RedditClient,
    subreddit: str,
    last_created_utc: int,
) -> PollResult:
    items = client.fetch_new_posts(subreddit=subreddit, limit=100)
    new_items = [d for d in items if _created_utc(d) > last_created_utc]
    if not new_items:
        return PollResult([], last_created_utc)

    new_items.sort(key=_created_utc)  # oldest-first for nicer downstream ordering
    max_ts = max(_created_utc(d) for d in new_items)
    return PollResult(new_items, max_ts)


def poll_comments(
    client: RedditClient,
    subreddit: str,
    last_created_utc: int,
) -> PollResult:
    items = client.fetch_new_comments(subreddit=subreddit, limit=100)
    new_items = [d for d in items if _created_utc(d) > last_created_utc]
    if not new_items:
        return PollResult([], last_created_utc)

    new_items.sort(key=_created_utc)
    max_ts = max(_created_utc(d) for d in new_items)
    return PollResult(new_items, max_ts)

