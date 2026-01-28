import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, count, avg

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "reddit_stream")

spark = (
    SparkSession.builder
    .appName("reddit-aggregates-5m")
    .config("spark.mongodb.write.connection.uri", MONGO_URI)
    .getOrCreate()
)

# 1) Kafka stream (2 topics)
df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", "reddit_posts,reddit_comments")
    .option("startingOffsets", "latest")
    .load()
)

# timestamp kafka natif (Spark l'a déjà)
events = df.select(
    col("timestamp").alias("kafka_ts"),
    col("topic").cast("string").alias("topic"),
    col("value").cast("string").alias("json_str")
)

# ✅ Rolling metric minimale: volume par fenêtre 5 minutes
metrics_5m = (
    events
    .withWatermark("kafka_ts", "10 minutes")
    .groupBy(window(col("kafka_ts"), "5 minutes"), col("topic"))
    .agg(count("*").alias("volume"))
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("topic"),
        col("volume")
    )
)

def write_mongo(batch_df, batch_id):
    (batch_df.write.format("mongodb")
        .mode("append")
        .option("database", MONGO_DB)
        .option("collection", "agg_5m_volume")
        .save()
    )

query = (
    metrics_5m.writeStream
    .outputMode("append")
    .foreachBatch(write_mongo)
    .option("checkpointLocation", "/tmp/chk_agg_5m_volume")
    .start()
)

query.awaitTermination()
