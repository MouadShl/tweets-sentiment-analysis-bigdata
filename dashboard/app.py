import os
from pymongo import MongoClient
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Reddit Streaming Dashboard", layout="wide")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "reddit_stream")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

st.title("📊 Reddit Streaming Dashboard (Kafka → Spark → MongoDB)")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Raw docs", db.raw_reddit.count_documents({}))
col2.metric("Processed docs", db.processed_reddit.count_documents({}))
col3.metric("Edges", db.reddit_edges.count_documents({}))
col4.metric("Nodes (graph_metrics)", db.graph_metrics.count_documents({}))

st.divider()

# Top 10 centrality
st.subheader("🏆 Top 10 users by weighted degree")
top_degree = list(db.graph_metrics.find({}, {"_id":0, "node":1, "degree_w":1, "in_degree_w":1, "out_degree_w":1}).sort("degree_w", -1).limit(10))
st.dataframe(pd.DataFrame(top_degree), use_container_width=True)

st.subheader("🌉 Top 10 users by betweenness")
top_between = list(db.graph_metrics.find({}, {"_id":0, "node":1, "betweenness":1, "degree_w":1}).sort("betweenness", -1).limit(10))
st.dataframe(pd.DataFrame(top_between), use_container_width=True)

st.divider()

# Community summary
st.subheader("👥 Top communities by size")
top_comm = list(db.graph_community_summary.find({}, {"_id":0, "community":1, "size":1}).sort("size", -1).limit(10))
st.dataframe(pd.DataFrame(top_comm), use_container_width=True)

st.divider()

# Sentiment distribution
st.subheader("🙂 Sentiment distribution (processed_reddit)")
pipeline = [
    {"$match": {"sentiment.label": {"$exists": True}}},
    {"$group": {"_id": "$sentiment.label", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
sent = list(db.processed_reddit.aggregate(pipeline))
df_sent = pd.DataFrame([{"label": x["_id"], "count": x["count"]} for x in sent])
st.bar_chart(df_sent.set_index("label"))

st.divider()

# Network image
st.subheader("🕸️ Network snapshot")
img_path = os.path.join("outputs", "network_snapshot.png")
if os.path.exists(img_path):
    st.image(img_path, caption="Top-degree subgraph snapshot", use_container_width=True)
else:
    st.warning("Image not found: outputs/network_snapshot.png (run visualize_network.py)")
