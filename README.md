## Tweets sentiment analysis — Person 1 (Ingestion)

This repo contains a **Docker-first** ingestion stack that:

- Scrapes Reddit using the **public JSON endpoints** (no API keys)
- Produces JSON messages into Kafka topics:
  - `reddit_posts`
  - `reddit_comments`

### Prerequisites

- Docker + Docker Compose

### Run

From the repo root:

```bash
docker compose up -d --build
```

### Run locally (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run the collector module
cd collector
python -m src.main
```

### Verify data is flowing

- **Kafka UI**: open `http://localhost:18080`
  - Cluster: `local`
  - Topics: `reddit_posts`, `reddit_comments`
- **Collector logs**:

```bash
docker compose logs -f collector
```

### Configuration

Edit in `docker-compose.yml` under the `collector` service:

- `SUBREDDITS`: comma-separated, e.g. `worldnews,news,dataisbeautiful`
- `POLL_INTERVAL_SECONDS`: e.g. `10`
- `USER_AGENT`: set a clear UA string
- `TOPIC_POSTS`, `TOPIC_COMMENTS`

Collector state (high-watermarks) is stored in a Docker volume (`collector_state`) so restarts do not re-emit old items.

### Message schemas

JSON schemas are in:

- `schemas/reddit_posts.schema.json`
- `schemas/reddit_comments.schema.json`



---

## Person 2 — Streaming ETL + Storage (Spark + MongoDB)

A starter Spark Structured Streaming job is included to:
- consume Kafka topics (`reddit_posts`, `reddit_comments`)
- clean/enrich text
- write to MongoDB collections (`raw_reddit`, `processed_reddit`, `aggregates_5m`)

See: `spark/README.md` and `mongodb/README.md`.
