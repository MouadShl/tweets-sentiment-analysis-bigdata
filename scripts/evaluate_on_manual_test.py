import os
import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

MANUAL = "data/processed/manual_test.csv"
MODEL_PATH = "models/sentiment_model.joblib"
OUT = "outputs/manual_eval_report.txt"

os.makedirs("outputs", exist_ok=True)

df = pd.read_csv(MANUAL).dropna(subset=["text", "true_label"])
df["true_label"] = df["true_label"].astype(str).str.strip().str.lower()

# Load your trained model
model = joblib.load(MODEL_PATH)
df["ml_pred"] = model.predict(df["text"].astype(str).tolist())

# VADER baseline
analyzer = SentimentIntensityAnalyzer()
def vader_label(c):
    if c >= 0.05: return "pos"
    if c <= -0.05: return "neg"
    return "neu"

df["vader_score"] = df["text"].astype(str).apply(lambda t: analyzer.polarity_scores(t)["compound"])
df["vader_pred"] = df["vader_score"].apply(vader_label)

# TextBlob baseline
df["tb_score"] = df["text"].astype(str).apply(lambda t: TextBlob(t).sentiment.polarity)
df["tb_pred"] = df["tb_score"].apply(lambda p: "pos" if p > 0.05 else ("neg" if p < -0.05 else "neu"))

labels = ["neg", "neu", "pos"]

def section(name, y_true, y_pred):
    rep = classification_report(y_true, y_pred, labels=labels, digits=4)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    s = f"\n==== {name} ====\n{rep}\nConfusion matrix (neg, neu, pos):\n{cm}\n"
    return s

report = ""
report += section("YOUR ML MODEL", df["true_label"], df["ml_pred"])
report += section("VADER", df["true_label"], df["vader_pred"])
report += section("TEXTBLOB", df["true_label"], df["tb_pred"])

with open(OUT, "w", encoding="utf-8") as f:
    f.write(report)

print("Saved:", OUT)
print(report)
