# 🚀 Real-Time Social Media Sentiment Analysis (Big Data & NLP)

![Apache Kafka](https://img.shields.io/badge/Kafka-Streaming-black?logo=apachekafka)
![Apache Spark](https://img.shields.io/badge/Spark-Structured%20Streaming-orange?logo=apachespark)
![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL-green?logo=mongodb)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)
![Python](https://img.shields.io/badge/Python-NLP-yellow?logo=python)

---

## 📌 Project Overview

This project implements a **fully containerized, end-to-end Big Data pipeline** for **real-time sentiment analysis of social media data (Reddit)**.

The system covers:
- Real-time data ingestion
- Stream processing
- Persistent storage
- NLP-based sentiment classification
- Topic extraction and insights

All components are orchestrated using **Docker Compose**, ensuring **reproducibility and portability across machines**.

---

## 🧠 Global Architecture

Reddit (Public JSON Endpoints)
↓
Collector (Python)
↓
Kafka Topics
(reddit_posts / reddit_comments)
↓
Spark Structured Streaming
↓
MongoDB
(posts, comments, analytics)
↓
Sentiment & Topic Insights

---

## 🧩 Team Contributions

### 👤 Mohamed Amine Azirgui — Data Ingestion & Streaming Backbone

**Responsibilities**
- Scraped Reddit using public JSON endpoints (no API keys)
- Produced structured JSON messages into Kafka topics:
  - `reddit_posts`
  - `reddit_comments`
- Designed a Docker-first ingestion stack
- Implemented Kafka health checks to guarantee safe startup order
- Persisted ingestion state to avoid duplicate data on restarts

**Technologies**
- Python  
- Apache Kafka  
- Docker & Docker Compose  

---

### 👤 Youssef Bouzit — Streaming ETL & Storage (Spark + MongoDB)

**Responsibilities**
- Implemented Spark Structured Streaming jobs consuming Kafka topics
- Cleaned, normalized, and enriched text streams
- Persisted raw and processed data into MongoDB
- Built time-based aggregations
- Solved Windows/Hadoop compatibility issues by running Spark in Linux containers

**Technologies**
- Apache Spark (Structured Streaming)  
- Apache Kafka  
- MongoDB  
- Docker  

---

### 👤 Mouad Souhal — Sentiment Analysis & NLP Modeling

**Responsibilities**
- Built an automated NLP pipeline for posts and comments
- Classified sentiment into **positive / neutral / negative**
- Stored sentiment labels, confidence scores, timestamps, and model versions in MongoDB
- Applied text preprocessing and normalization
- Evaluated model performance and ensured reproducibility

**Technologies**
- Python  
- scikit-learn  
- NLP (TF-IDF, Bag-of-Words)  
- MongoDB  

---

### 👤 Abdoul Amine Kabirou Amusa — Topic Modeling, Insights & Reporting

**Responsibilities**
- Implemented topic extraction to explain sentiment context
- Applied **TF-IDF + NMF** for unsupervised topic modeling
- Identified dominant discussion themes per subreddit
- Analyzed sentiment trends and topic frequency over time
- Produced interpretable insights and summaries for reporting and presentation

**Technologies**
- Python  
- scikit-learn  
- NLP (TF-IDF, NMF)  
- Data Analysis & Visualization  

---

## 🧪 Validation & Debugging

The pipeline was validated with **real evidence**, not just running containers:

- Kafka topics manually listed and consumed from earliest offsets
- JSON message schemas verified
- MongoDB queried from inside the container using `mongosh`
- Document counts and collections validated
- Spark stabilized using Docker-based Linux execution

---

## ▶️ How to Run the Project

### Prerequisites
- Docker
- Docker Compose

### Run the full pipeline
```bash
docker compose up -d --build
