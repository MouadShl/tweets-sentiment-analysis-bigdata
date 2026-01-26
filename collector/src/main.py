import logging
import os
import time
from .config import CollectorConfig
from .kafka_client import KafkaTopics, build_producer, send_json
from .normalizers import normalize_comment, normalize_post
from .poller import poll_comments, poll_posts
from .reddit_client import RedditClient
from .state import load_state, save_state
from .timeutil import utc_iso


def main() -> None:
    cfg = CollectorConfig.from_env()
    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    log = logging.getLogger("collector")
    topics = KafkaTopics(posts=cfg.topic_posts, comments=cfg.topic_comments)
    state_path = os.path.join(cfg.state_dir, "state.json")

    reddit = RedditClient(user_agent=cfg.user_agent)
    producer = build_producer(cfg.kafka_bootstrap_servers)
    state = load_state(state_path)

    log.info("Starting collector. subreddits=%s interval=%ss", cfg.subreddits, cfg.poll_interval_seconds)
    log.info(
        "Kafka bootstrap=%s posts_topic=%s comments_topic=%s",
        cfg.kafka_bootstrap_servers,
        topics.posts,
        topics.comments,
    )
    log.info("State file=%s", state_path)

    while True:
        any_progress = False
        for sr in cfg.subreddits:
            try:
                # Posts
                last_post_ts = int(state.last_post_created_utc.get(sr, 0))
                post_res = poll_posts(reddit, sr, last_post_ts)
                if post_res.new_items:
                    ingested_at = utc_iso()
                    for p in post_res.new_items:
                        msg = normalize_post(p, ingested_at=ingested_at)
                        key = msg.get("fullname") or msg.get("id") or ""
                        send_json(producer, topics.posts, value=msg, key=key)
                    producer.flush(timeout=10)
                    state.last_post_created_utc[sr] = post_res.new_high_watermark
                    any_progress = True
                    log.info(
                        "r/%s posts: +%d (last_created_utc=%d)",
                        sr,
                        len(post_res.new_items),
                        post_res.new_high_watermark,
                    )

                # Comments
                last_comment_ts = int(state.last_comment_created_utc.get(sr, 0))
                comment_res = poll_comments(reddit, sr, last_comment_ts)
                if comment_res.new_items:
                    ingested_at = utc_iso()
                    for c in comment_res.new_items:
                        msg = normalize_comment(c, ingested_at=ingested_at)
                        key = msg.get("fullname") or msg.get("id") or ""
                        send_json(producer, topics.comments, value=msg, key=key)
                    producer.flush(timeout=10)
                    state.last_comment_created_utc[sr] = comment_res.new_high_watermark
                    any_progress = True
                    log.info(
                        "r/%s comments: +%d (last_created_utc=%d)",
                        sr,
                        len(comment_res.new_items),
                        comment_res.new_high_watermark,
                    )

            except Exception:
                log.exception("Error processing r/%s", sr)

        if any_progress:
            try:
                save_state(state_path, state)
            except Exception:
                log.exception("Failed to save state")

        time.sleep(cfg.poll_interval_seconds)


if __name__ == "__main__":
    main()

