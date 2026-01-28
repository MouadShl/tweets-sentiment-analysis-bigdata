import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_timestamp, from_unixtime, lower, regexp_replace, trim, concat_ws,
    window, count, avg
)
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, IntegerType, BooleanType
)

"""Person 2 — Streaming ETL + Storage (Spark Structured Streaming + MongoDB)

- Read Kafka topics: reddit_posts, reddit_comments
- Parse JSON messages
- Clean + enrich columns
- Write to MongoDB collections:
  - raw_reddit
  - processed_reddit
  - aggregates_5m (rolling metrics, 5-minute windows)

Env vars (defaults are for local dev):
  KAFKA_BOOTSTRAP_SERVERS=localhost:29092
  MONGO_URI=mongodb://localhost:27017
  MONGO_DB=reddit_stream
  TOPICS=reddit_posts,reddit_comments
  CHECKPOINT_DIR=checkpoints
  WINDOW_DURATION="5 minutes"
  WATERMARK="10 minutes"
"""

# -----------------------------
# Config
# -----------------------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB = os.getenv("MONGO_DB", "reddit_stream")
TOPICS = os.getenv("TOPICS", "reddit_posts,reddit_comments")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "checkpoints")
WINDOW_DURATION = os.getenv("WINDOW_DURATION", "5 minutes")
WATERMARK = os.getenv("WATERMARK", "10 minutes")

spark = (
    SparkSession.builder
    .appName("reddit-kafka-to-mongo")
    .config("spark.mongodb.write.connection.uri", MONGO_URI)
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# -----------------------------
# Schemas (match repo JSON schema)
# -----------------------------
post_schema = StructType([
    StructField("schema_version", IntegerType(), True),
    StructField("source", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("ingested_at", StringType(), True),

    StructField("id", StringType(), True),
    StructField("fullname", StringType(), True),
    StructField("subreddit", StringType(), True),
    StructField("subreddit_id", StringType(), True),
    StructField("author", StringType(), True),
    StructField("created_utc", LongType(), True),

    StructField("title", StringType(), True),
    StructField("selftext", StringType(), True),
    StructField("url", StringType(), True),
    StructField("permalink", StringType(), True),

    StructField("num_comments", IntegerType(), True),
    StructField("score", IntegerType(), True),
    StructField("over_18", BooleanType(), True),
    StructField("is_self", BooleanType(), True),
])

comment_schema = StructType([
    StructField("schema_version", IntegerType(), True),
    StructField("source", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("ingested_at", StringType(), True),

    StructField("id", StringType(), True),
    StructField("fullname", StringType(), True),
    StructField("subreddit", StringType(), True),
    StructField("subreddit_id", StringType(), True),
    StructField("author", StringType(), True),
    StructField("created_utc", LongType(), True),

    StructField("body", StringType(), True),
    StructField("permalink", StringType(), True),
    StructField("link_id", StringType(), True),
    StructField("parent_id", StringType(), True),
    StructField("score", IntegerType(), True),
])

# -----------------------------
# Read Kafka (value is JSON string)
# -----------------------------
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", TOPICS)
    .option("startingOffsets", "latest")
    .load()
)

base = kafka_df.select(
    col("topic"),
    col("timestamp").alias("kafka_ts"),
    col("value").cast("string").alias("json_str"),
)

posts_raw = (
    base.filter(col("topic") == "reddit_posts")
    .withColumn("data", from_json(col("json_str"), post_schema))
    .select("topic", "kafka_ts", col("data.*"))
)

comments_raw = (
    base.filter(col("topic") == "reddit_comments")
    .withColumn("data", from_json(col("json_str"), comment_schema))
    .select("topic", "kafka_ts", col("data.*"))
)

raw_all = posts_raw.unionByName(comments_raw, allowMissingColumns=True)

# -----------------------------
# Enrich: event_ts + text field + basic cleaning
# -----------------------------
# Convert epoch seconds -> timestamp (UTC)
enriched = raw_all.withColumn("event_ts", to_timestamp(from_unixtime(col("created_utc"))))

# Build text:
# - posts: title + selftext
# - comments: body
enriched = enriched.withColumn(
    "text",
    concat_ws(" ", col("title").cast("string"), col("selftext").cast("string"), col("body").cast("string"))
)

# Clean text: lowercase, remove URLs, remove non-alnum, collapse whitespace
processed = (
    enriched
    .withColumn("text", lower(col("text")))
    .withColumn("text", regexp_replace(col("text"), r"http\S+|www\S+", ""))
    .withColumn("text", regexp_replace(col("text"), r"[^a-z0-9\s]", " "))
    .withColumn("text", regexp_replace(col("text"), r"\s+", " "))
    .withColumn("text", trim(col("text")))
    .select(
        "topic", "kafka_ts", "event_ts",
        "schema_version", "source", "event_type", "ingested_at",
        "id", "fullname", "subreddit", "subreddit_id", "author", "created_utc",
        "title", "selftext", "body", "url", "permalink", "link_id", "parent_id",
        "num_comments", "score", "over_18", "is_self",
        "text"
    )
    .filter(col("id").isNotNull())
)

# -----------------------------
# Mongo write helper
# -----------------------------
def write_mongo(batch_df, epoch_id, collection):
    (
        batch_df.write
        .format("mongodb")
        .mode("append")
        .option("database", DB)
        .option("collection", collection)
        .save()
    )

# -----------------------------
# Write streams: raw, processed
# -----------------------------
raw_query = (
    raw_all.writeStream
    .foreachBatch(lambda df, eid: write_mongo(df, eid, "raw_reddit"))
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/raw_reddit")
    .start()
)

processed_query = (
    processed.writeStream
    .foreachBatch(lambda df, eid: write_mongo(df, eid, "processed_reddit"))
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/processed_reddit")
    .start()
)

# -----------------------------
# Rolling aggregates (Gold table): 5 minute windows
# -----------------------------
aggregates = (
    processed
    .withWatermark("event_ts", WATERMARK)
    .groupBy(
        window(col("event_ts"), WINDOW_DURATION),
        col("topic"),
        col("subreddit"),
    )
    .agg(
        count("*").alias("volume"),
        avg(col("score").cast("double")).alias("avg_score"),
    )
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        "topic", "subreddit", "volume", "avg_score"
    )
)

agg_query = (
    aggregates.writeStream
    .outputMode("update")
    .foreachBatch(lambda df, eid: write_mongo(df, eid, "aggregates_5m"))
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/aggregates_5m")
    .start()
)

spark.streams.awaitAnyTermination()
