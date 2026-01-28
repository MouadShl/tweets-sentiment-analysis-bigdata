import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

INP = "data/processed/manual_test.csv"
OUT = "data/processed/manual_test.csv"  # overwrite

df = pd.read_csv(INP)
analyzer = SentimentIntensityAnalyzer()

def vader_label(text):
    c = analyzer.polarity_scores(str(text))["compound"]
    if c >= 0.05: return "pos"
    if c <= -0.05: return "neg"
    return "neu"

df["true_label"] = df["text"].fillna("").apply(vader_label)
df.to_csv(OUT, index=False, encoding="utf-8")
print("Prefilled labels using VADER:", OUT)
print(df["true_label"].value_counts())
