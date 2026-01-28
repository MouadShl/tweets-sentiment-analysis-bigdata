import os, re, html
import pandas as pd

INPUT = "data/processed/sample_comments.csv"   # you already have this
OUT   = "data/processed/manual_test.csv"
N = 100

def clean_text(t: str) -> str:
    t = "" if pd.isna(t) else str(t)

    # fix common mojibake like donÔÇÖt (best effort without extra libs)
    try:
        t = t.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        pass

    t = html.unescape(t)                          # &gt; etc
    t = re.sub(r"http\S+", "", t)                 # remove URLs
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t) # markdown links [txt](url) -> txt
    t = re.sub(r"\s+", " ", t).strip()            # normalize spaces
    return t

df = pd.read_csv(INPUT)

df = df.dropna(subset=["id", "text"]).copy()
df["text"] = df["text"].apply(clean_text)
df = df[df["text"].str.len() >= 10]

sample = df.sample(n=min(N, len(df)), random_state=42)[["id", "text"]].copy()
sample["true_label"] = ""   # YOU fill: pos / neu / neg

os.makedirs("data/processed", exist_ok=True)
sample.to_csv(OUT, index=False, encoding="utf-8")
print("Saved:", OUT, "rows:", len(sample))
print(sample.head(5).to_string(index=False))
