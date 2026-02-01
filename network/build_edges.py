import os
import re
from datetime import datetime, timezone
from pymongo import MongoClient, UpdateOne

# -------- Config (prend tes variables d'env si tu veux, sinon defaults local) --------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "reddit_stream")

SOURCE_COLL = os.getenv("SOURCE_COLL", "processed_reddit")
EDGES_COLL = os.getenv("EDGES_COLL", "reddit_edges")

# Regex mentions Reddit : "u/username" ou "/u/username"
MENTION_RE = re.compile(r"(?:^|[\s(])(?:u/|/u/)([A-Za-z0-9_-]{3,20})", re.IGNORECASE)

def clean_user(u: str) -> str | None:
    if not u:
        return None
    u = u.strip()
    if u.lower() in {"[deleted]", "deleted", "none", "null"}:
        return None
    return u

def main():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    src = db[SOURCE_COLL]
    edges = db[EDGES_COLL]

    # Index utiles (rapides, safe)
    src.create_index("fullname")
    src.create_index("topic")
    src.create_index("parent_id")
    src.create_index("author")
    edges.create_index([("src", 1), ("dst", 1), ("edge_type", 1)], unique=True)

    now = datetime.now(timezone.utc)

    # Cache pour éviter des lookups Mongo trop coûteux
    fullname_to_author = {}

    def get_author_by_fullname(fullname: str) -> str | None:
        if not fullname:
            return None
        if fullname in fullname_to_author:
            return fullname_to_author[fullname]

        doc = src.find_one({"fullname": fullname}, {"author": 1})
        author = clean_user(doc.get("author")) if doc else None
        fullname_to_author[fullname] = author
        return author

    # On ne traite que les commentaires (eux ont parent_id)
    cursor = src.find(
        {"topic": "reddit_comments", "parent_id": {"$ne": None}},
        {"author": 1, "parent_id": 1, "text": 1, "event_ts": 1}
    ).batch_size(500)

    ops = []
    count_comments = 0
    count_edges = 0

    for doc in cursor:
        count_comments += 1

        author = clean_user(doc.get("author"))
        if not author:
            continue

        event_ts = doc.get("event_ts") or now

        # -------- Edge Type 1 : reply (author -> parent_author) --------
        parent_fullname = doc.get("parent_id")  # ex: "t1_xxx" ou "t3_xxx"
        parent_author = get_author_by_fullname(parent_fullname)

        if parent_author and parent_author != author:
            ops.append(
                UpdateOne(
                    {"src": author, "dst": parent_author, "edge_type": "reply"},
                    {
                        "$inc": {"weight": 1},
                        "$setOnInsert": {"first_seen": event_ts},
                        "$set": {"last_seen": event_ts},
                    },
                    upsert=True,
                )
            )
            count_edges += 1

        # -------- Edge Type 2 : mention (author -> mentioned_user) --------
        text = doc.get("text") or ""
        for m in set(MENTION_RE.findall(text)):
            mentioned = clean_user(m)
            if mentioned and mentioned != author:
                ops.append(
                    UpdateOne(
                        {"src": author, "dst": mentioned, "edge_type": "mention"},
                        {
                            "$inc": {"weight": 1},
                            "$setOnInsert": {"first_seen": event_ts},
                            "$set": {"last_seen": event_ts},
                        },
                        upsert=True,
                    )
                )
                count_edges += 1

        # Flush par batch
        if len(ops) >= 1000:
            edges.bulk_write(ops, ordered=False)
            ops.clear()

    if ops:
        edges.bulk_write(ops, ordered=False)

    print("✅ Done")
    print(f"Comments scanned: {count_comments}")
    print(f"Edges upserts:    {count_edges}")
    print(f"Edges collection: {MONGO_DB}.{EDGES_COLL}")

if __name__ == "__main__":
    main()
