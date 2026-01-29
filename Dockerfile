FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Worker needs scripts + models + (optional) nlp package if it's used in imports
COPY scripts /app/scripts
COPY models /app/models

# If your worker imports from collector/src, copy it too:
COPY collector/src /app/collector_src

COPY .env /app/.env

CMD ["python", "scripts/mongo_sentiment_worker.py"]
