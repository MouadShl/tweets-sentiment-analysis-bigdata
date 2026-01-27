import os, json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

INPUT = "data/processed/sample_comments.csv"
OUT_JSON = "outputs/topics.json"

os.makedirs("outputs", exist_ok=True)

df = pd.read_csv(INPUT).dropna(subset=["text"]).copy()
texts = df["text"].astype(str).tolist()

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    max_features=20000,
    ngram_range=(1,2),
    min_df=2
)
X = vectorizer.fit_transform(texts)

N_TOPICS = 8
nmf = NMF(n_components=N_TOPICS, random_state=42)
W = nmf.fit_transform(X)
H = nmf.components_
terms = vectorizer.get_feature_names_out()

topics = []
for i in range(N_TOPICS):
    top_idx = H[i].argsort()[-12:][::-1]
    keywords = [terms[j] for j in top_idx]

    # pick 3 example comments most related to topic
    top_docs = W[:, i].argsort()[-3:][::-1]
    examples = [texts[k][:220] for k in top_docs]

    topics.append({"topic_id": i, "keywords": keywords, "examples": examples})

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(topics, f, ensure_ascii=False, indent=2)

print("Saved:", OUT_JSON)
for t in topics:
    print(f"Topic {t['topic_id']}: {', '.join(t['keywords'][:7])}")
