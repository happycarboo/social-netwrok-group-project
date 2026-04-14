"""Final publication-quality network visualisations."""

import ast
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np

CODES_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CODES_DIR, "..", "congress_network")
FIG_DIR = os.path.join(CODES_DIR, "figures")
RES_DIR = os.path.join(CODES_DIR, "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

PARTY_COLORS = {"Democrat": "#1f77b4", "Republican": "#d62728", "Independent": "#2ca02c"}


def load_graph():
    G = nx.DiGraph()
    with open(os.path.join(DATA_DIR, "congress.edgelist"), encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            u, v, d = s.split(maxsplit=2)
            w = float(ast.literal_eval(d).get("weight", 1.0))
            G.add_edge(int(u), int(v), weight=w)
    return G


def load_users():
    try:
        import openpyxl
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
        import openpyxl
    wb = openpyxl.load_workbook(os.path.join(DATA_DIR, "users.xlsx"))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    users = {}
    for row in rows[1:]:
        d = dict(zip(header, row))
        users[int(d["id"])] = d
    return users


def load_vc_scores():
    vc_path = os.path.join(DATA_DIR, "viral_centrality_scores.csv")
    if not os.path.exists(vc_path):
        return {}
    scores = {}
    with open(vc_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores[int(row["node_id"])] = float(row["viral_centrality"])
    return scores


def main():
    G = load_graph()
    users = load_users()
    vc_scores = load_vc_scores()

    nodes = list(G.nodes())
    G_ud = G.to_undirected()

    print("Computing layout...")
    pos = nx.spring_layout(G_ud, seed=42, k=0.18, iterations=100)

    # === Figure 1: Party coloured, size = out-strength ===
    out_str = np.array([
        sum(d for _, _, d in G.out_edges(n, data="weight", default=0)) for n in nodes
    ])
    max_s = out_str.max() if out_str.max() > 0 else 1
    node_sizes_str = 15 + 250 * (out_str / max_s)
    party_colors = [PARTY_COLORS.get(users.get(n, {}).get("Party", ""), "#aec7e8") for n in nodes]

    fig, ax = plt.subplots(figsize=(16, 12))
    nx.draw_networkx_edges(G, pos, alpha=0.025, width=0.25, edge_color="gray", arrows=False, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=party_colors, node_size=list(node_sizes_str),
                           alpha=0.9, linewidths=0.3, edgecolors="white", ax=ax)

    # Label top 10 by VC
    if vc_scores:
        top10 = sorted(vc_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        labels = {n: users.get(n, {}).get("Users", str(n)) for n, _ in top10}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, font_weight="bold", ax=ax)

    for party, color in PARTY_COLORS.items():
        ax.scatter([], [], c=color, label=party, s=80)
    ax.legend(fontsize=12, loc="lower right", title="Party")
    ax.set_title("Congressional Twitter Influence Network\n(node size = out-strength, colour = party)", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "07_network_party_strength.png"), dpi=220)
    plt.close()
    print("Saved: figures/07_network_party_strength.png")

    # === Figure 2: VC score as node colour (viridis) ===
    vc_vals = np.array([vc_scores.get(n, 0) for n in nodes])
    norm = mcolors.Normalize(vmin=vc_vals.min(), vmax=vc_vals.max())
    cmap = cm.viridis
    vc_colors = [cmap(norm(v)) for v in vc_vals]
    node_sizes_vc = 15 + 220 * (vc_vals / vc_vals.max() if vc_vals.max() > 0 else 1)

    fig, ax = plt.subplots(figsize=(16, 12))
    nx.draw_networkx_edges(G, pos, alpha=0.025, width=0.25, edge_color="gray", arrows=False, ax=ax)
    sc = nx.draw_networkx_nodes(G, pos, node_color=vc_colors, node_size=list(node_sizes_vc),
                                alpha=0.9, linewidths=0.3, edgecolors="white", ax=ax)

    if vc_scores:
        top10 = sorted(vc_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        labels = {n: users.get(n, {}).get("Users", str(n)) for n, _ in top10}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, font_weight="bold", ax=ax)

    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="Viral Centrality Score", shrink=0.6)
    ax.set_title("Congressional Twitter Influence Network\n(node colour & size = Viral Centrality)", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "07_network_viral_centrality.png"), dpi=220)
    plt.close()
    print("Saved: figures/07_network_viral_centrality.png")


if __name__ == "__main__":
    main()
