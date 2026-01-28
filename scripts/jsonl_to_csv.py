import json, os
import pandas as pd

IN_PATH = "data/raw/reddit_comments.jsonl"
OUT_PATH = "data/processed/sample_comments.csv"

rows = []
with open(IN_PATH, "r", encoding="utf-16") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)

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
            "ingested_at": d.get("ingested_at"),
            "text": text,
        })

df = pd.DataFrame(rows).drop_duplicates(subset=["id"])
os.makedirs("data/processed", exist_ok=True)
df.to_csv(OUT_PATH, index=False)

print("Saved:", OUT_PATH, "rows:", len(df))
print(df[["subreddit","author","score","text"]].head(3).to_string(index=False))
