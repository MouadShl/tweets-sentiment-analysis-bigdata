# Person 2 — Spark Structured Streaming → MongoDB

This folder adds the **Streaming ETL + Storage** layer:

- Consume Kafka topics: `reddit_posts`, `reddit_comments`
- Parse JSON, clean text, enrich columns
- Write to MongoDB:
  - `raw_reddit`
  - `processed_reddit`
  - `aggregates_5m` (rolling metrics, 5-minute windows)

## 1) Start the stack (Kafka + Collector + MongoDB)

From repo root:

```bash
docker compose up -d --build
```

MongoDB will be available at `mongodb://localhost:27017`.

## 2) Run the Spark streaming job (local)

### Prereqs
- Java 11+ (or 17)
- Spark 3.x installed (pyspark)
- Python 3.10+

From repo root:

```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  spark/jobs/stream_reddit_to_mongo.py
```

### Common env vars

```bash
export KAFKA_BOOTSTRAP_SERVERS=localhost:29092
export MONGO_URI=mongodb://localhost:27017
export MONGO_DB=reddit_stream
```

## 3) Verify in MongoDB

```bash
mongosh
use reddit_stream
show collections
db.raw_reddit.countDocuments()
db.processed_reddit.countDocuments()
db.aggregates_5m.find().sort({window_start:-1}).limit(5)
```

## Notes

- Event time is based on `created_utc` (epoch seconds).
- Aggregates use watermarking (`10 minutes`) + 5-minute windows.
