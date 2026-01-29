import os
import time
from datetime import datetime, timezone

import joblib
from pymongo import MongoClient, UpdateOne

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_text(doc: dict) -> str:
    """
    Robust text extractor for both reddit comments and posts.
    Adjust fields if your Mongo schema uses different names.
    """
    # comments
    for k in ("text", "body"):
        v = doc.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # posts (title + selftext)
    title = doc.get("title") or ""
    selftext = doc.get("selftext") or doc.get("content") or ""
    combo = (str(title).strip() + "\n" + str(selftext).strip()).strip()
    return combo


def load_model(model_path: str):
    model = joblib.load(model_path)
    # must have predict(); predict_proba() is optional
    return model


def process_collection_once(col, model, model_version: str, batch_size: int) -> int:
    """
    Fetch docs missing sentiment, predict, and update.
    Returns number of updated docs.
    """
    query = {"sentiment.label": {"$exists": False}}
    projection = {
        "_id": 1,
        "text": 1,
        "body": 1,
        "title": 1,
        "selftext": 1,
        "created_utc": 1,
        "subreddit": 1,
    }

    docs = list(col.find(query, projection).limit(batch_size))
    if not docs:
        return 0

    texts = []
    ids = []
    empty_ids = []

    for d in docs:
        t = extract_text(d)
        if not t:
            empty_ids.append(d["_id"])
            continue
        ids.append(d["_id"])
        texts.append(t)

    ops = []

    # If text is empty, mark as neutral with reason
    now = utc_now_iso()
    for _id in empty_ids:
        ops.append(
            UpdateOne(
                {"_id": _id, "sentiment.label": {"$exists": False}},
                {"$set": {
                    "sentiment": {
                        "label": "neu",
                        "model_version": model_version,
                        "predicted_at": now,
                        "note": "empty_text",
                    }
                }},
            )
        )

    # Predict for non-empty
    if texts:
        labels = model.predict(texts)

        proba = None
        proba_labels = None
        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(texts)
                # sklearn classifiers usually have .classes_
                proba_labels = list(getattr(model, "classes_", []))
            except Exception:
                proba = None

        for _id, t, lab, i in zip(ids, texts, labels, range(len(texts))):
            payload = {
                "label": str(lab),
                "model_version": model_version,
                "predicted_at": now,
                "text_len": len(t),
            }

            if proba is not None and proba_labels:
                row = proba[i]
                payload["proba"] = {str(c): float(p) for c, p in zip(proba_labels, row)}
                payload["confidence"] = float(max(row))

            ops.append(
                UpdateOne(
                    {"_id": _id, "sentiment.label": {"$exists": False}},
                    {"$set": {"sentiment": payload}},
                )
            )

    if not ops:
        return 0

    res = col.bulk_write(ops, ordered=False)
    return res.modified_count


def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "reddit_stream")
    collections = os.getenv("MONGO_COLLECTIONS", "comments").split(",")

    model_path = os.getenv("SENTIMENT_MODEL_PATH", "models/sentiment_model.joblib")
    model_version = os.getenv("MODEL_VERSION", "tfidf_logreg_v1")
    batch_size = int(os.getenv("BATCH_SIZE", "200"))
    sleep_seconds = int(os.getenv("SLEEP_SECONDS", "2"))

    print("[worker] connecting:", mongo_uri)
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("[worker] mongo OK")

    model = load_model(model_path)
    print("[worker] model loaded:", model_path)

    db = client[mongo_db]
    cols = [db[c.strip()] for c in collections if c.strip()]

    while True:
        total = 0
        for col in cols:
            updated = process_collection_once(col, model, model_version, batch_size)
            total += updated
            if updated:
                print(f"[worker] updated {updated} docs in {col.name}")

        if total == 0:
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
import certifi
from pymongo import MongoClient

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=8000
)
client.admin.command("ping")
