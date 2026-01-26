## READ FIRST (Team setup)

This repo runs a **Reddit → Kafka** ingestion pipeline:

- A Python collector polls Reddit public JSON endpoints (no API keys)
- Messages are produced into Kafka topics:
  - `reddit_posts`
  - `reddit_comments`

### 1) Prerequisites (install once)

- **Docker Desktop** (Mac/Windows) or Docker Engine (Linux)
- Make sure Docker is running (you can test with `docker ps`)

### 2) First run (one command)

From the repo root:

```bash
docker compose up -d --build
```

### 3) Verify it works

#### A) Collector logs

```bash
docker compose logs -f collector
```

You should see lines like:
- `r/worldnews posts: +...`
- `r/worldnews comments: +...`

#### B) Kafka UI (recommended)

Open:
- `http://localhost:18080`

Then:
- Topics → `reddit_posts` / `reddit_comments` → Messages

#### C) Consume a few messages from Kafka (optional)

```bash
docker exec -it tsa-kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic reddit_posts \
  --from-beginning \
  --max-messages 5
```

### 4) Common configuration

Edit `docker-compose.yml` → `collector.environment`:
- `SUBREDDITS`: e.g. `AskReddit,worldnews,news`
- `POLL_INTERVAL_SECONDS`: e.g. `10`
- `USER_AGENT`: keep a clear string (recommended)

### 5) Stop / reset

Stop containers:

```bash
docker compose down
```

Full reset (also deletes saved collector state so it replays fresh):

```bash
docker compose down -v
```

### Troubleshooting

- **Docker daemon not running**:
  - Error: `Cannot connect to the Docker daemon ...`
  - Fix: start Docker Desktop and retry.

- **Port already in use**:
  - Kafka UI uses host port **18080**.
  - If you still see `bind: address already in use`, change the port mapping in `docker-compose.yml`.

