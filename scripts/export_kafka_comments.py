import json, os
import pandas as pd
from kafka import KafkaConsumer

BOOTSTRAP = os.getenv("BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("TOPIC", "reddit_comments")
MAX_MSG = int(os.getenv("MAX_MSG", "2000"))

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP,
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    consumer_timeout_ms=15000,
)

rows = []
for msg in consumer:
    d = msg.value

    # Your JSON uses "body" (seen in your output)
    text = (d.get("body") or "").strip()
    if len(text) < 5:
        continue

    rows.append({
        "id": d.get("id"),
        "created_utc": d.get("created_utc"),
        "subreddit": d.get("subreddit"),
        "author": d.get("author"),
        "score": d.get("score", 0),
        "link_id": d.get("link_id"),
        "parent_id": d.get("parent_id"),
        "permalink": d.get("permalink"),
        "event_type": d.get("event_type"),
        "ingested_at": d.get("ingested_at"),
        "text": text,
    })

    if len(rows) >= MAX_MSG:
        break

df = pd.DataFrame(rows).drop_duplicates(subset=["id"])
os.makedirs("data/processed", exist_ok=True)
out = "data/processed/sample_comments.csv"
df.to_csv(out, index=False)

print("Saved:", out, "rows:", len(df))
print(df[["subreddit", "author", "score", "text"]].head(3).to_string(index=False))
