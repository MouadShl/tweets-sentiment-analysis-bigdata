## Trello cards (reconstructed from repo)

Use this file to create Trello cards (each section can be a card; each checklist item can be a Trello checklist item).

### Card: Ingestion stack (Docker + Kafka) — DONE

- [x] Add `docker-compose.yml` with Zookeeper + Kafka (single broker dev defaults)
- [x] Add Kafka UI service and expose it on host port `18080`
- [x] Configure Kafka listeners for both container network (`kafka:9092`) and host access (`localhost:29092`)
- [x] Add healthcheck for Kafka and gate dependent services on it

### Card: Reddit collector service — DONE

- [x] Implement Python collector entrypoint loop (`collector/src/main.py`)
- [x] Fetch Reddit data using public JSON endpoints (no API keys) (`collector/src/reddit_client.py`)
- [x] Poll new posts and comments per subreddit and filter by `created_utc` high-watermark (`collector/src/poller.py`)
- [x] Normalize raw Reddit payloads into a consistent message shape (`collector/src/normalizers.py`)
- [x] Produce messages to Kafka topics (`collector/src/kafka_client.py`)
- [x] Use message keys (prefer `fullname`, fallback to `id`) for partitioning consistency
- [x] Store collector state (high-watermarks) on disk and persist via Docker volume (`collector/src/state.py` + `collector_state` volume)
- [x] Make collector configurable via env vars (`collector/src/config.py`)
- [x] Containerize the collector (`collector/Dockerfile`) and run it under Compose
- [x] Add restart policy (`unless-stopped`) for collector reliability

### Card: Message schemas + examples — DONE

- [x] Define JSON schema for `reddit_posts` (`schemas/reddit_posts.schema.json`)
- [x] Define JSON schema for `reddit_comments` (`schemas/reddit_comments.schema.json`)
- [x] Add example payloads for posts/comments (`schemas/examples/reddit_post.example.json`, `schemas/examples/reddit_comment.example.json`)

### Card: Developer docs / onboarding — DONE

- [x] Write run instructions (`README.md`)
- [x] Write team “run this first” guide + troubleshooting (`READFIRST.md`)
- [x] Provide env template defaults (`.env.example`)

### Card: Verification checklist — DONE

- [x] Start the stack: `docker compose up -d --build`
- [x] Confirm collector is running: `docker compose logs -f collector`
- [x] Confirm topics have messages via Kafka UI at `http://localhost:18080`
- [x] (Optional) Consume from Kafka inside container (example in `READFIRST.md`)

---

## Backlog / next cards (from `project.txt` + gaps)

### Card: Airflow orchestration (Person 1) — TODO

- [ ] Add an Airflow service to `docker-compose.yml` (local dev)
- [ ] Create a basic DAG to start/monitor ingestion jobs (at minimum: health + “is collector producing”)
- [ ] Document how to run Airflow locally and how the team should use it

### Card: Data model expansion — TODO

- [ ] Add a `reddit_edges` topic for reply/interaction edges (user A → user B) if needed for network analysis
- [ ] Define JSON schema for edges (and example payloads)

### Card: Robustness improvements — TODO

- [ ] Add backoff / retry strategy for Reddit HTTP 429/5xx responses
- [ ] Add timeouts and error classification (network vs rate-limit vs invalid payload)
- [ ] Add structured logging fields (subreddit, topic, counts, watermarks)

### Card: Data quality guardrails — TODO

- [ ] Validate normalized events against JSON schema before producing (fail-fast or route to DLQ topic)
- [ ] Add a “dead-letter” topic for bad messages (e.g., `reddit_dlq`)

### Card: Testing + CI — TODO

- [ ] Add unit tests for poll filtering and normalizers
- [ ] Add CI workflow to run tests + basic linting
- [ ] Add pre-commit config (format + lint + tests)

### Card: Observability (nice-to-have) — TODO

- [ ] Add a lightweight health endpoint (or heartbeat logs) for the collector
- [ ] Export basic metrics (items produced, errors, rate-limits) (Prometheus or logs-only)

