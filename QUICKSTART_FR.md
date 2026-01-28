# QUICKSTART — Projet complet (Kafka + Collector + MongoDB + Spark Streaming)

Ce repo contient :
- **Collector Reddit → Kafka** (docker compose)
- **MongoDB** (docker compose)
- **Spark Structured Streaming** (lancé en local) :
  - Kafka → parse JSON → nettoyage texte → enrichissements
  - écrit dans Mongo : `raw_reddit`, `processed_reddit`, `aggregates_5m`

## 1) Prérequis (Mac)
- Docker Desktop
- Homebrew
- Java 17 + Spark

Installer Java + Spark :
```bash
brew install openjdk@17 apache-spark
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
spark-submit --version
```

## 2) Démarrer l'infra (Kafka + collector + Mongo)
À la racine du projet :
```bash
docker compose down --remove-orphans
docker compose up -d --build
docker compose ps
```

Kafka UI :
- http://localhost:18080

## 3) Vérifier que le collector envoie des messages
```bash
docker compose logs -f collector
```
(CTRL+C pour arrêter)

## 4) Lancer Spark Streaming (Kafka → Mongo)
Toujours à la racine :
```bash
export KAFKA_BOOTSTRAP="localhost:29092"
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="reddit_stream"

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  spark/jobs/stream_reddit_to_mongo.py
```

> Si ta version Spark n’est pas **3.5.1**, remplace `3.5.1` par la version affichée par `spark-submit --version`.

## 5) Vérifier MongoDB (résultats)
Dans un autre terminal :
```bash
docker exec -it tsa-mongodb mongosh
```
Puis :
```js
use reddit_stream
show collections

db.raw_reddit.countDocuments()
db.processed_reddit.countDocuments()
db.aggregates_5m.countDocuments()

db.aggregates_5m.find().sort({ window_start: -1 }).limit(5)
```

## 6) Créer les indexes Mongo (important)
Depuis la racine du projet :
```bash
docker exec -i tsa-mongodb mongosh < mongodb/create_indexes.js
```

## Collections “Gold” (pour dashboard)
- `aggregates_5m` : volume + avg_score par fenêtre de 5 minutes (par subreddit + topic)
