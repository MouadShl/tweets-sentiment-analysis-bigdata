# scripts/mongo_sentiment_worker.py
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError
import joblib


# --------- Config (env vars) ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "reddit")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "comments")  # e.g. "comments" or "posts"

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
SLEEP_SECONDS = float(os.getenv("SLEEP_SECONDS", "2"))

MODEL_PATH = os.getenv("SENTIMENT_MODEL_PATH", "models/sentiment_model.joblib")
MODEL_VERSION = os.getenv("MODEL_VERSION", "tfidf_logreg_v1")


# If your model predicts numeric classes, map them here
# If your model already predicts strings "neg/neu/pos", this is ignored.
CLASS_MAP = {0: "neg", 1: "neu", 2: "pos"}


def extract_text(doc: Dict[str, Any]) -> str:
    """
    Robust text extraction for both comments and posts.
    Adjust keys depending on how Person2 stores data in MongoDB.
    """
    # Comment-like
    if doc.get("text"):
        return str(doc.get("text") or "")
    if doc.get("body"):
        return str(doc.get("body") or "")

    # Post-like
    title = doc.get("title") or ""
    selftext = doc.get("selftext") or doc.get("content") or ""
    text = (str(title) + "\n" + str(selftext)).strip()
    return text


def safe_predict(model, texts: List[str]) -> Dict[str, Any]:
    """
    Returns:
      labels: list[str] in {"neg","neu","pos"}
      probs: list[dict] with keys neg/neu/pos when available
    """
    preds = model.predict(texts)

    # Convert to strings if needed
    labels = []
    for p in preds:
        if isinstance(p, (int, float)) and int(p) in CLASS_MAP:
            labels.append(CLASS_MAP[int(p)])
        else:
            labels.append(str(p))

    probs_out: List[Optional[Dict[str, float]]] = [None] * len(texts)

    # If model supports predict_proba, store probabilities
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(texts)

        # Get class order
        classes = getattr(model, "classes_", None)
        # If pipeline, classes_ might be inside the last step
        if classes is None and hasattr(model, "named_steps"):
            last = list(model.named_steps.values())[-1]
            classes = getattr(last, "classes_", None)

        if classes is not None:
            classes = [str(c) if not isinstance(c, (int, float)) else CLASS_MAP.get(int(c), str(c)) for c in classes]

        for i in range(len(texts)):
            row = proba[i]
            if classes and len(classes) == len(row):
                probs_out[i] = {classes[j]: float(row[j]) for j in range(len(row))}
            else:
                # fallback: assume neg/neu/pos order
                if len(row) == 3:
                    probs_out[i] = {"neg": float(row[0]), "neu": float(row[1]), "pos": float(row[2])}

    return {"labels": labels, "probs": probs_out}


def build_update_payload(label: str, prob: Optional[Dict[str, float]], text: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    extra = {
        "text_len": len(text),
        "word_count": len(text.split()),
    }
    sentiment_doc = {
        "label": label,
        "proba": prob,  # can be None
        "model_version": MODEL_VERSION,
        "scored_at": now,
    }
    return {
        "$set": {
            "sentiment": sentiment_doc,
            "nlp_meta": extra,
            "updated_at": now,
        }
    }


def process_batch(col) -> int:
    """
    Fetch a batch of docs that are not scored yet; score; update in MongoDB.
    Returns number processed.
    """
    query = {
        # only docs that have not been scored
        "sentiment.label": {"$exists": False},
        # ensure doc actually has some text fields
        "$or": [{"text": {"$exists": True}}, {"body": {"$exists": True}}, {"title": {"$exists": True}}],
    }

    docs = list(col.find(query, {"_id": 1, "text": 1, "body": 1, "title": 1, "selftext": 1}).limit(BATCH_SIZE))
    if not docs:
        return 0

    texts = [extract_text(d) for d in docs]
    # avoid empty texts
    texts = [t if t else "" for t in texts]

    pred = safe_predict(MODEL, texts)

    processed = 0
    for d, label, prob, text in zip(docs, pred["labels"], pred["probs"], texts):
        # Avoid race condition: only update if still missing label
        filter_q = {"_id": d["_id"], "sentiment.label": {"$exists": False}}
        update = build_update_payload(label, prob, text)
        res = col.update_one(filter_q, update)
        processed += int(res.modified_count)

    return processed


def run_forever():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    col = db[MONGO_COLLECTION]

    print(f"[worker] Connected to {MONGO_URI} db={MONGO_DB} col={MONGO_COLLECTION}")
    print(f"[worker] Model: {MODEL_PATH} (version={MODEL_VERSION})")

    while True:
        try:
            n = process_batch(col)
            if n == 0:
                time.sleep(SLEEP_SECONDS)
            else:
                print(f"[worker] processed={n}")
        except PyMongoError as e:
            print(f"[worker] Mongo error: {e}")
            time.sleep(3)
        except Exception as e:
            print(f"[worker] Unexpected error: {e}")
            time.sleep(3)


# Load model once (fast)
MODEL = joblib.load(MODEL_PATH)

if __name__ == "__main__":
    run_forever()
