"""Network overview: basic statistics and full-network visualisation."""

import csv
import json

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from utils import (load_graph, load_users, party_of, PARTY_COLORS,
                   FIG_DIR, RES_DIR, save_fig)


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())
    N = G.number_of_nodes()
    M = G.number_of_edges()

    # --- Basic stats ---
    print("=== Network Overview ===")
    density = nx.density(G)
    reciprocity = nx.reciprocity(G)

    G_ud = G.to_undirected()
    n_wcc = nx.number_weakly_connected_components(G)
    n_scc = nx.number_strongly_connected_components(G)
    largest_scc = max(nx.strongly_connected_components(G), key=len)

    largest_scc_sub = G.subgraph(largest_scc)
    avg_path = nx.average_shortest_path_length(largest_scc_sub)
    diameter = nx.diameter(largest_scc_sub)
    avg_clustering = nx.average_clustering(G_ud)

    avg_degree = M / N
    avg_weight = sum(d["weight"] for _, _, d in G.edges(data=True)) / M

    stats = {
        "nodes": N,
        "directed_edges": M,
        "avg_in_out_degree": round(avg_degree, 2),
        "avg_edge_weight": round(avg_weight, 6),
        "graph_density": round(density, 4),
        "reciprocity": round(reciprocity, 4),
        "weakly_connected_components": n_wcc,
        "strongly_connected_components": n_scc,
        "largest_scc_size": len(largest_scc),
        "diameter": diameter,
        "avg_path_length": round(avg_path, 2),
        "avg_clustering_coefficient": round(avg_clustering, 4),
    }

    for k, v in stats.items():
        print(f"  {k}: {v}")

    with open(f"{RES_DIR}/network_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("  Saved: results/network_stats.json")

    # --- Party breakdown ---
    party_counts = {}
    for p in ["Democrat", "Republican", "Other"]:
        party_counts[p] = sum(1 for n in nodes if party_of(users, n) == p)
    print("\n  Party breakdown:")
    for p, c in party_counts.items():
        print(f"    {p}: {c} ({c/N*100:.1f}%)")

    with open(f"{RES_DIR}/party_breakdown.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["party", "count", "share"])
        for p, c in party_counts.items():
            w.writerow([p, c, round(c / N, 4)])

    # --- House vs Senate breakdown ---
    chamber_counts = {}
    for n in nodes:
        ch = users.get(n, {}).get("Chamber", None) or "Unknown"
        if ch not in chamber_counts:
            chamber_counts[ch] = 0
        chamber_counts[ch] += 1
    print("\n  Chamber breakdown:")
    for ch, c in sorted(chamber_counts.items()):
        print(f"    {ch}: {c} ({c/N*100:.1f}%)")

    with open(f"{RES_DIR}/chamber_breakdown.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chamber", "count", "share"])
        for ch, c in sorted(chamber_counts.items()):
            w.writerow([ch, c, round(c / N, 4)])

    # --- Figure 1: Network coloured by party ---
    print("\nComputing layout (spring)...")
    pos = nx.spring_layout(G_ud, seed=42, k=0.18, iterations=80)

    # Save layout for reuse
    np.savez(f"{RES_DIR}/layout.npz",
             nodes=np.array(nodes),
             x=np.array([pos[n][0] for n in nodes]),
             y=np.array([pos[n][1] for n in nodes]))

    node_colors = [PARTY_COLORS[party_of(users, n)] for n in nodes]
    out_str = [sum(d for _, _, d in G.out_edges(n, data="weight", default=0)) for n in nodes]
    sizes = [8 + 60 * s for s in out_str]

    fig, ax = plt.subplots(figsize=(12, 9))
    nx.draw_networkx_edges(G, pos, alpha=0.03, width=0.3, edge_color="gray",
                           arrows=False, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                           node_size=sizes, alpha=0.85, linewidths=0, ax=ax)
    for party, color in PARTY_COLORS.items():
        ax.scatter([], [], c=color, label=party, s=70)
    ax.legend(fontsize=11, loc="lower right")
    ax.set_title("Congressional Twitter Network\n(node size = out-strength, colour = party)")
    ax.axis("off")
    save_fig(fig, "01_network_overview.png")

    print("\nDone: 01_network_overview.py")


if __name__ == "__main__":
    main()
