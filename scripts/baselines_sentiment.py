import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

df = pd.read_csv("data/processed/sample_comments.csv")
analyzer = SentimentIntensityAnalyzer()

def vader_label(c):
    if c >= 0.05: return "pos"
    if c <= -0.05: return "neg"
    return "neu"

vader_scores = df["text"].fillna("").apply(lambda t: analyzer.polarity_scores(t)["compound"])
df["vader_score"] = vader_scores
df["vader_label"] = df["vader_score"].apply(vader_label)

tb_scores = df["text"].fillna("").apply(lambda t: TextBlob(t).sentiment.polarity)
df["textblob_score"] = tb_scores
df["textblob_label"] = df["textblob_score"].apply(lambda p: "pos" if p>0.05 else ("neg" if p<-0.05 else "neu"))

df.to_csv("data/processed/comments_with_baselines.csv", index=False)

print("Saved: data/processed/comments_with_baselines.csv")
print(df[["vader_label","textblob_label"]].value_counts().head(10))
