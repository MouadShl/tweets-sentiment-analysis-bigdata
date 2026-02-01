import os
from collections import Counter

from pymongo import MongoClient
import networkx as nx

import community as community_louvain  # python-louvain


def build_graph_from_mongo(mongo_uri: str, db_name: str, edge_collection: str = "reddit_edges"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    edges = list(db[edge_collection].find({}, {"_id": 0, "src": 1, "dst": 1, "weight": 1}))

    print(f"[louvain] edges loaded: {len(edges)} from {db_name}.{edge_collection}")

    G = nx.Graph()
    for e in edges:
        src = e.get("src")
        dst = e.get("dst")
        w = e.get("weight", 1)
        if src and dst:
            # undirected graph for louvain
            if G.has_edge(src, dst):
                G[src][dst]["weight"] += w
            else:
                G.add_edge(src, dst, weight=w)

    print(f"[louvain] nodes={G.number_of_nodes()} edges={G.number_of_edges()}")
    return G, client


def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "reddit_stream")

    G, client = build_graph_from_mongo(mongo_uri, db_name)
    db = client[db_name]

    # Louvain partition: node -> community_id
    print("[louvain] running best_partition() ...")
    partition = community_louvain.best_partition(G, weight="weight", random_state=42)

    # Community sizes
    sizes = Counter(partition.values())
    print(f"[louvain] communities found: {len(sizes)}")
    top_sizes = sizes.most_common(10)

    # Compute modularity (quality score)
    modularity = community_louvain.modularity(partition, G, weight="weight")
    print(f"[louvain] modularity: {modularity:.4f}")

    # Save node communities to Mongo
    nodes_docs = [{"node": n, "community": int(c)} for n, c in partition.items()]
    db["graph_communities"].delete_many({})
    if nodes_docs:
        db["graph_communities"].insert_many(nodes_docs)

    # Save summary
    summary_docs = [{"community": int(cid), "size": int(sz)} for cid, sz in sizes.items()]
    db["graph_community_summary"].delete_many({})
    if summary_docs:
        db["graph_community_summary"].insert_many(summary_docs)

    db["graph_run_info"].insert_one({
        "algo": "louvain",
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "communities": len(sizes),
        "modularity": float(modularity),
        "top10_sizes": [{"community": int(cid), "size": int(sz)} for cid, sz in top_sizes]
    })

    print("✅ Saved to Mongo:")
    print(f" - {db_name}.graph_communities (node -> community)")
    print(f" - {db_name}.graph_community_summary (community -> size)")
    print(f" - {db_name}.graph_run_info (run metadata)")
    print("\nTop 10 communities by size:")
    for cid, sz in top_sizes:
        print(f"  community {cid:<5} size={sz}")


if __name__ == "__main__":
    main()
