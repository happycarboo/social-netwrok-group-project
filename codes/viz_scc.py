# -*- coding: utf-8 -*-
"""Visualise the 7 SCCs on the full network layout."""

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

from utils import (load_graph, load_users, party_of, username_of,
                   PARTY_COLORS, CLR_DEM, CLR_REP, CLR_NEUTRAL,
                   FIG_DIR, RES_DIR, save_fig)


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())

    # Load saved layout
    d = np.load(f"{RES_DIR}/layout.npz", allow_pickle=True)
    pos = {int(n): (x, y) for n, x, y in zip(d["nodes"], d["x"], d["y"])}

    sccs = sorted(nx.strongly_connected_components(G), key=len, reverse=True)
    big_scc = sccs[0]
    small_sccs = [s for s in sccs[1:]]
    isolated_nodes = set()
    for s in small_sccs:
        isolated_nodes |= s

    # --- Figure: Full network highlighting the 6 isolated nodes ---
    fig, ax = plt.subplots(figsize=(13, 10))

    # Draw edges lightly
    nx.draw_networkx_edges(G, pos, alpha=0.02, width=0.2, edge_color="gray",
                           arrows=False, ax=ax)

    # Draw big SCC nodes coloured by party
    big_nodes = [n for n in nodes if n in big_scc]
    big_colors = [PARTY_COLORS[party_of(users, n)] for n in big_nodes]
    nx.draw_networkx_nodes(G, pos, nodelist=big_nodes, node_color=big_colors,
                           node_size=15, alpha=0.5, linewidths=0, ax=ax)

    # Draw isolated SCC nodes as large highlighted markers
    iso_list = list(isolated_nodes)
    iso_colors = [PARTY_COLORS[party_of(users, n)] for n in iso_list]
    nx.draw_networkx_nodes(G, pos, nodelist=iso_list, node_color=iso_colors,
                           node_size=250, alpha=1.0, linewidths=2,
                           edgecolors="black", ax=ax)

    # Draw edges FROM isolated nodes to the big SCC in yellow
    iso_edges = [(u, v) for u, v in G.edges() if u in isolated_nodes and v in big_scc]
    nx.draw_networkx_edges(G, pos, edgelist=iso_edges, edge_color="gold",
                           width=1.5, alpha=0.8, arrows=True, arrowsize=8, ax=ax)

    # Label isolated nodes
    iso_labels = {n: username_of(users, n) for n in iso_list}
    for n in iso_list:
        x, y = pos[n]
        ax.annotate(iso_labels[n], (x, y), fontsize=8, fontweight="bold",
                    xytext=(8, 8), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", alpha=0.8))

    # Legend
    for party, color in PARTY_COLORS.items():
        ax.scatter([], [], c=color, label=party, s=50)
    ax.scatter([], [], c="white", edgecolors="black", linewidths=2, s=120,
              label="Isolated SCC (size=1)")
    ax.plot([], [], color="gold", linewidth=2, label="One-way edges (no reply)")
    ax.legend(fontsize=9, loc="lower right")

    ax.set_title("Strongly Connected Components\n"
                 "Main SCC = 469 nodes (faded) | 6 isolated nodes (highlighted)\n"
                 "Gold arrows = outgoing edges from isolated members (nobody replies back)",
                 fontsize=11)
    ax.axis("off")
    save_fig(fig, "scc_visualization.png")

    print("Done: viz_scc.py")


if __name__ == "__main__":
    main()
