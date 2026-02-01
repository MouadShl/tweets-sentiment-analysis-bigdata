import os
import random
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pymongo import MongoClient


def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "reddit_stream")
    sample_nodes = int(os.getenv("SAMPLE_NODES", "300"))  # tu peux monter à 500 après

    print(f"[viz] connecting to {mongo_uri} db={db_name}")
    client = MongoClient(mongo_uri)
    db = client[db_name]

    edges = list(db["reddit_edges"].find({}, {"_id": 0, "src": 1, "dst": 1, "weight": 1}))
    comms = {d["node"]: d["community"] for d in db["graph_communities"].find({}, {"_id": 0, "node": 1, "community": 1})}

    print(f"[viz] edges loaded: {len(edges)}")
    print(f"[viz] communities loaded: {len(comms)}")

    # Build undirected graph
    G = nx.Graph()
    for e in edges:
        s, t = e.get("src"), e.get("dst")
        w = int(e.get("weight", 1))
        if s and t:
            if G.has_edge(s, t):
                G[s][t]["weight"] += w
            else:
                G.add_edge(s, t, weight=w)

    print(f"[viz] full graph: nodes={G.number_of_nodes()} edges={G.number_of_edges()}")

    # --- sample a subgraph to keep plot readable
       # Prefer a dense sample: take top nodes by weighted degree
    deg_full = dict(G.degree(weight="weight"))
    nodes_sorted = sorted(deg_full.items(), key=lambda x: x[1], reverse=True)
    top_nodes = [n for n, d in nodes_sorted[:sample_nodes]]

    H = G.subgraph(top_nodes).copy()
    print(f"[viz] top-degree subgraph: nodes={H.number_of_nodes()} edges={H.number_of_edges()}")


    # Node attributes: community + degree
    for n in H.nodes():
        H.nodes[n]["community"] = comms.get(n, -1)

    degree = dict(H.degree(weight="weight"))

    # Save nodes/edges CSV for dashboard
    os.makedirs("outputs", exist_ok=True)

    nodes_df = pd.DataFrame({
        "node": list(H.nodes()),
        "community": [H.nodes[n]["community"] for n in H.nodes()],
        "degree_w": [degree.get(n, 0) for n in H.nodes()],
    }).sort_values("degree_w", ascending=False)

    edges_df = pd.DataFrame([
        {"src": u, "dst": v, "weight": d.get("weight", 1),
         "src_comm": H.nodes[u]["community"], "dst_comm": H.nodes[v]["community"]}
        for u, v, d in H.edges(data=True)
    ])

    nodes_path = "outputs/network_nodes_sample.csv"
    edges_path = "outputs/network_edges_sample.csv"
    nodes_df.to_csv(nodes_path, index=False)
    edges_df.to_csv(edges_path, index=False)

    print(f"✅ Saved: {nodes_path}")
    print(f"✅ Saved: {edges_path}")

    # --- Plot snapshot (no fancy colors, just sizes)
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(H, seed=42, k=0.35)

    sizes = [max(20, min(800, degree.get(n, 0) * 2)) for n in H.nodes()]
    nx.draw_networkx_edges(H, pos, alpha=0.25, width=0.6)
    nx.draw_networkx_nodes(H, pos, node_size=sizes, alpha=0.85)

    plt.title(f"Reddit Interaction Network (sample={H.number_of_nodes()} nodes)")
    plt.axis("off")

    img_path = "outputs/network_snapshot.png"
    plt.tight_layout()
    plt.savefig(img_path, dpi=200)
    print(f"✅ Saved: {img_path}")

    print("\nTIP: If the plot is too dense, reduce SAMPLE_NODES (e.g. 200).")


if __name__ == "__main__":
    main()
