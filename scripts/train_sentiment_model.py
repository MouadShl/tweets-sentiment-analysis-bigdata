import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import joblib

INPUT = "data/processed/comments_with_baselines.csv"
OUT_MODEL = "models/sentiment_model.joblib"
OUT_REPORT = "outputs/sentiment_report.txt"

os.makedirs("models", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

df = pd.read_csv(INPUT)

# Use VADER as weak label for training
df = df.dropna(subset=["text", "vader_label"])
df["label"] = df["vader_label"].astype(str)

X = df["text"].astype(str)
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1,2),
        max_features=50000
    )),
    ("clf", LogisticRegression(
        max_iter=200,
        n_jobs=None
    ))
])

model.fit(X_train, y_train)
pred = model.predict(X_test)

report = classification_report(y_test, pred, digits=4)
cm = confusion_matrix(y_test, pred, labels=["neg", "neu", "pos"])

print(report)
print("Confusion matrix (neg, neu, pos):\n", cm)

with open(OUT_REPORT, "w", encoding="utf-8") as f:
    f.write(report + "\n")
    f.write("Confusion matrix (neg, neu, pos):\n")
    f.write(str(cm) + "\n")

joblib.dump(model, OUT_MODEL)
print("Saved model:", OUT_MODEL)
print("Saved report:", OUT_REPORT)
