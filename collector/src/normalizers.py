from __future__ import annotations

from typing import Any, Dict


def normalize_post(d: Dict[str, Any], ingested_at: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "source": "reddit_public_json",
        "event_type": "post",
        "ingested_at": ingested_at,
        "id": d.get("id"),
        "fullname": d.get("name"),  # t3_xxx
        "subreddit": d.get("subreddit"),
        "subreddit_id": d.get("subreddit_id"),
        "author": d.get("author"),
        "created_utc": d.get("created_utc"),
        "title": d.get("title"),
        "selftext": d.get("selftext"),
        "url": d.get("url"),
        "permalink": d.get("permalink"),
        "num_comments": d.get("num_comments"),
        "score": d.get("score"),
        "over_18": d.get("over_18"),
        "is_self": d.get("is_self"),
    }


def normalize_comment(d: Dict[str, Any], ingested_at: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "source": "reddit_public_json",
        "event_type": "comment",
        "ingested_at": ingested_at,
        "id": d.get("id"),
        "fullname": d.get("name"),  # t1_xxx
        "subreddit": d.get("subreddit"),
        "subreddit_id": d.get("subreddit_id"),
        "author": d.get("author"),
        "created_utc": d.get("created_utc"),
        "body": d.get("body"),
        "permalink": d.get("permalink"),
        "link_id": d.get("link_id"),  # t3_xxx
        "parent_id": d.get("parent_id"),  # t1_... or t3_...
        "score": d.get("score"),
    }

