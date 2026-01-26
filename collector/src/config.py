from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


@dataclass(frozen=True)
class CollectorConfig:
    kafka_bootstrap_servers: str
    topic_posts: str
    topic_comments: str

    subreddits: list[str]
    poll_interval_seconds: float
    user_agent: str

    state_dir: str
    log_level: str

    @staticmethod
    def from_env() -> "CollectorConfig":
        subreddits = [s.strip() for s in env("SUBREDDITS", "news").split(",") if s.strip()]
        return CollectorConfig(
            kafka_bootstrap_servers=env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            topic_posts=env("TOPIC_POSTS", "reddit_posts"),
            topic_comments=env("TOPIC_COMMENTS", "reddit_comments"),
            subreddits=subreddits,
            poll_interval_seconds=float(env("POLL_INTERVAL_SECONDS", "10")),
            user_agent=env("USER_AGENT", "tsa-reddit-collector/1.0 (class project)"),
            state_dir=env("STATE_DIR", "/state"),
            log_level=env("LOG_LEVEL", "INFO").upper(),
        )

