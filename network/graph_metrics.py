import os
from pymongo import MongoClient
import pandas as pd
import networkx as nx

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "reddit_stream")
EDGES_COLLECTION = os.getenv("EDGES_COLLECTION", "reddit_edges")

def main():
    print(f"[metrics] connecting to {MONGO_URI} db={MONGO_DB}")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[MONGO_DB]

    edges = list(db[EDGES_COLLECTION].find({}, {"_id": 0, "src": 1, "dst": 1, "weight": 1, "edge_type": 1}))
    print(f"[metrics] edges loaded: {len(edges)}")

    # Directed graph (reply/mention are directional)
    G = nx.DiGraph()
    for e in edges:
        src, dst = e["src"], e["dst"]
        w = int(e.get("weight", 1))
        if G.has_edge(src, dst):
            G[src][dst]["weight"] += w
        else:
            G.add_edge(src, dst, weight=w, edge_type=e.get("edge_type", "reply"))

    print(f"[metrics] nodes={G.number_of_nodes()} edges={G.number_of_edges()}")

    in_deg = dict(G.in_degree(weight="weight"))
    out_deg = dict(G.out_degree(weight="weight"))
    deg = dict(G.degree(weight="weight"))

    n = G.number_of_nodes()
    k = min(500, n)  # sample size for speed if big
    bet = nx.betweenness_centrality(G, k=k, seed=42, weight="weight") if n > 500 else nx.betweenness_centrality(G, weight="weight")

    df = pd.DataFrame({
        "node": list(G.nodes()),
        "in_degree_w": [in_deg.get(x, 0) for x in G.nodes()],
        "out_degree_w": [out_deg.get(x, 0) for x in G.nodes()],
        "degree_w": [deg.get(x, 0) for x in G.nodes()],
        "betweenness": [bet.get(x, 0.0) for x in G.nodes()],
    }).sort_values("degree_w", ascending=False)

    os.makedirs("outputs", exist_ok=True)
    df.head(50).to_csv("outputs/top50_centrality.csv", index=False)
    print("✅ Saved: outputs/top50_centrality.csv")

    coll = db["graph_metrics"]
    coll.delete_many({})
    coll.insert_many(df.to_dict("records"))
    print("✅ Saved to Mongo: reddit_stream.graph_metrics")

    print("\nTop 10 nodes by weighted degree:")
    print(df.head(10)[["node", "degree_w", "in_degree_w", "out_degree_w", "betweenness"]])

if __name__ == "__main__":
    main()
