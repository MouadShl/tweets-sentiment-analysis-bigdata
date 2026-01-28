from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "reddit_stream"
SRC_COLLECTION = "processed_reddit"
DST_COLLECTION = "scored_reddit"

analyzer = SentimentIntensityAnalyzer()

def vader_compound(text: str):
    if text is None:
        return None
    t = text.strip()
    if not t:
        return None
    return float(analyzer.polarity_scores(t)["compound"])

vader_compound_udf = F.udf(vader_compound, DoubleType())

def label(compound: float):
    if compound is None:
        return None
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"

label_udf = F.udf(label, StringType())

def main():
    spark = (
        SparkSession.builder
        .appName("sentiment-to-mongo")
        .config("spark.mongodb.read.connection.uri", MONGO_URI)
        .config("spark.mongodb.write.connection.uri", MONGO_URI)
        .getOrCreate()
    )

    df = (
        spark.read.format("mongodb")
        .option("database", MONGO_DB)
        .option("collection", SRC_COLLECTION)
        .load()
    )

    df2 = (
        df.filter(F.col("text").isNotNull() & (F.length(F.col("text")) > 0))
          .withColumn("sentiment_compound", vader_compound_udf(F.col("text")))
          .withColumn("sentiment_label", label_udf(F.col("sentiment_compound")))
          .withColumn("scored_at", F.current_timestamp())
    )

    # IMPORTANT: pour éviter les doublons à chaque relance, on fait un overwrite (simple)
    (
        df2.write.format("mongodb")
        .option("database", MONGO_DB)
        .option("collection", DST_COLLECTION)
        .mode("overwrite")
        .save()
    )

    spark.stop()

if __name__ == "__main__":
    main()
