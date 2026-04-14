# -*- coding: utf-8 -*-
"""
Egocentric Network Analysis
Compare ego networks of the top Republican vs top Democrat influencer.
"""

import json

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from utils import (load_graph, load_users, party_of, username_of,
                   PARTY_COLORS, FIG_DIR, RES_DIR, save_fig)


def ego_stats(G, ego, users):
    """Compute stats for a 1-hop ego network."""
    neighbors = set(G.predecessors(ego)) | set(G.successors(ego))
    ego_nodes = neighbors | {ego}
    sub = G.subgraph(ego_nodes)

    party_counts = {}
    for n in neighbors:
        p = party_of(users, n)
        party_counts[p] = party_counts.get(p, 0) + 1

    out_w = sum(d["weight"] for _, _, d in G.out_edges(ego, data=True))
    in_w = sum(d["weight"] for _, _, d in G.in_edges(ego, data=True))

    ego_party = party_of(users, ego)
    same_party = party_counts.get(ego_party, 0)
    cross_party = sum(v for k, v in party_counts.items() if k != ego_party)

    return {
        "username": username_of(users, ego),
        "party": ego_party,
        "neighbors": len(neighbors),
        "out_degree": G.out_degree(ego),
        "in_degree": G.in_degree(ego),
        "out_strength": round(out_w, 4),
        "in_strength": round(in_w, 4),
        "neighbor_party": party_counts,
        "same_party_neighbors_pct": round(same_party / len(neighbors) * 100, 1) if neighbors else 0,
        "cross_party_neighbors_pct": round(cross_party / len(neighbors) * 100, 1) if neighbors else 0,
        "ego_density": round(nx.density(sub), 4),
    }


def draw_ego(G, ego, users, ax, title):
    """Draw ego network on given axis."""
    neighbors = set(G.predecessors(ego)) | set(G.successors(ego))
    ego_nodes = neighbors | {ego}
    sub = G.subgraph(ego_nodes).copy()

    pos = nx.spring_layout(sub, seed=42, k=0.5)

    node_colors = []
    node_sizes = []
    for n in sub.nodes():
        if n == ego:
            node_colors.append("gold")
            node_sizes.append(200)
        else:
            node_colors.append(PARTY_COLORS[party_of(users, n)])
            node_sizes.append(30)

    weights = [sub[u][v].get("weight", 0.001) * 12 for u, v in sub.edges()]

    nx.draw_networkx_edges(sub, pos, width=weights, alpha=0.3,
                           edge_color="gray", arrows=True, arrowsize=5, ax=ax)
    nx.draw_networkx_nodes(sub, pos, node_color=node_colors,
                           node_size=node_sizes, alpha=0.85, ax=ax)

    ego_label = {ego: username_of(users, ego)}
    nx.draw_networkx_labels(sub, pos, labels=ego_label,
                            font_size=8, font_weight="bold", ax=ax)
    ax.set_title(title, fontsize=10)
    ax.axis("off")


def main():
    G = load_graph()
    users = load_users()

    # Pick top Republican and top Democrat by VC
    import csv
    vc = {}
    with open(f"{RES_DIR}/viral_centrality_scores.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vc[int(row["node_id"])] = float(row["viral_centrality"])

    nodes = list(G.nodes())
    dem_top = max((n for n in nodes if party_of(users, n) == "Democrat"),
                  key=lambda n: vc.get(n, 0))
    rep_top = max((n for n in nodes if party_of(users, n) == "Republican"),
                  key=lambda n: vc.get(n, 0))

    print("=" * 60)
    print("Egocentric Network Analysis")
    print("=" * 60)

    stats = {}
    for label, ego in [("top_republican", rep_top), ("top_democrat", dem_top)]:
        s = ego_stats(G, ego, users)
        stats[label] = s
        print(f"\n  {s['username']} ({s['party']}):")
        print(f"    Neighbors: {s['neighbors']}")
        print(f"    Out-degree: {s['out_degree']}, In-degree: {s['in_degree']}")
        print(f"    Out-strength: {s['out_strength']}, In-strength: {s['in_strength']}")
        print(f"    Same-party neighbors: {s['same_party_neighbors_pct']}%")
        print(f"    Cross-party neighbors: {s['cross_party_neighbors_pct']}%")
        print(f"    Ego density: {s['ego_density']}")
        print(f"    Neighbor parties: {s['neighbor_party']}")

    with open(f"{RES_DIR}/egocentric_stats.json", "w") as f:
        json.dump(stats, f, indent=2, default=str)

    # Figure: side-by-side ego networks + party composition pies
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    draw_ego(G, rep_top, users, axes[0, 0],
             f"(A) Ego: {username_of(users, rep_top)} (Republican)")
    draw_ego(G, dem_top, users, axes[0, 1],
             f"(B) Ego: {username_of(users, dem_top)} (Democrat)")

    # Pie charts of neighbor party composition
    for idx, (label, ego) in enumerate([("top_republican", rep_top), ("top_democrat", dem_top)]):
        ax = axes[1, idx]
        s = stats[label]
        parties = list(s["neighbor_party"].keys())
        counts = [s["neighbor_party"][p] for p in parties]
        colors = [PARTY_COLORS.get(p, "#999999") for p in parties]
        labels = [f"{p}\n({c})" for p, c in zip(parties, counts)]
        ax.pie(counts, labels=labels, colors=colors, autopct="%1.1f%%",
               startangle=90, textprops={"fontsize": 9})
        panel = "(C)" if idx == 0 else "(D)"
        ax.set_title(f"{panel} Neighbors of {s['username']}")

    fig.suptitle("Egocentric Network Comparison", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "06_egocentric.png")

    print("\nDone: 06_egocentric.py")


if __name__ == "__main__":
    main()
