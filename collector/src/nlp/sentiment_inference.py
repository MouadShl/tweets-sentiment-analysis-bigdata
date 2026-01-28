import joblib

MODEL_PATH = "models/sentiment_model.joblib"
_model = joblib.load(MODEL_PATH)

def predict_sentiment(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "neu"
    return str(_model.predict([text])[0])
