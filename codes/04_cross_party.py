"""Cross-party influence analysis and bridging nodes."""

import ast
import csv
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

CODES_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CODES_DIR, "..", "congress_network")
FIG_DIR = os.path.join(CODES_DIR, "figures")
RES_DIR = os.path.join(CODES_DIR, "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)


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


def main():
    G = load_graph()
    users = load_users()

    node_party = {n: users.get(n, {}).get("Party", "Unknown") for n in G.nodes()}

    parties = ["Democrat", "Republican"]

    # Party-to-party flow matrix
    flow_count = defaultdict(float)
    flow_weight = defaultdict(float)

    for u, v, d in G.edges(data=True):
        src_party = node_party.get(u, "Unknown")
        tgt_party = node_party.get(v, "Unknown")
        key = (src_party, tgt_party)
        flow_count[key] += 1
        flow_weight[key] += d.get("weight", 0)

    print("\n=== Party-to-Party Edge Count ===")
    for p1 in parties:
        for p2 in parties:
            k = (p1, p2)
            print(f"  {p1} -> {p2}: {int(flow_count[k])} edges, total weight={flow_weight[k]:.4f}")

    # Build matrix for heatmap
    count_mat = np.array([[flow_count[(p1, p2)] for p2 in parties] for p1 in parties])
    weight_mat = np.array([[flow_weight[(p1, p2)] for p2 in parties] for p1 in parties])

    # Within vs cross ratio
    total_count = count_mat.sum()
    within = count_mat[0, 0] + count_mat[1, 1]
    cross = count_mat[0, 1] + count_mat[1, 0]
    print(f"\n  Within-party edges: {int(within)} ({within/total_count*100:.1f}%)")
    print(f"  Cross-party edges:  {int(cross)} ({cross/total_count*100:.1f}%)")

    # Save party stats
    with open(os.path.join(RES_DIR, "cross_party_stats.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_party", "target_party", "edge_count", "total_weight"])
        for p1 in parties:
            for p2 in parties:
                writer.writerow([p1, p2, int(flow_count[(p1, p2)]), round(flow_weight[(p1, p2)], 6)])

    # Heatmaps
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    im0 = axes[0].imshow(count_mat, cmap="Blues")
    axes[0].set_xticks([0, 1]); axes[0].set_yticks([0, 1])
    axes[0].set_xticklabels(parties); axes[0].set_yticklabels(parties)
    axes[0].set_xlabel("Target Party"); axes[0].set_ylabel("Source Party")
    axes[0].set_title("Edge Count by Party")
    for i in range(2):
        for j in range(2):
            axes[0].text(j, i, f"{int(count_mat[i,j])}", ha="center", va="center", fontsize=13)
    plt.colorbar(im0, ax=axes[0])

    im1 = axes[1].imshow(weight_mat, cmap="Reds")
    axes[1].set_xticks([0, 1]); axes[1].set_yticks([0, 1])
    axes[1].set_xticklabels(parties); axes[1].set_yticklabels(parties)
    axes[1].set_xlabel("Target Party"); axes[1].set_ylabel("Source Party")
    axes[1].set_title("Total Influence Weight by Party")
    for i in range(2):
        for j in range(2):
            axes[1].text(j, i, f"{weight_mat[i,j]:.2f}", ha="center", va="center", fontsize=12)
    plt.colorbar(im1, ax=axes[1])

    plt.suptitle("Cross-Party Influence Matrix")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "04_cross_party_heatmap.png"), dpi=200)
    plt.close()

    # Bridging nodes: nodes with high cross-party out-edges
    print("\nComputing bridging scores...")
    bridge_scores = {}
    for n in G.nodes():
        src_party = node_party.get(n, "Unknown")
        if src_party not in parties:
            continue
        cross_weight = sum(
            d.get("weight", 0)
            for _, v, d in G.out_edges(n, data=True)
            if node_party.get(v, "") != src_party and node_party.get(v, "") in parties
        )
        bridge_scores[n] = cross_weight

    top_bridgers = sorted(bridge_scores.items(), key=lambda x: x[1], reverse=True)[:20]

    with open(os.path.join(RES_DIR, "top_bridgers.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "username", "party", "chamber", "cross_party_out_weight"])
        for n, v in top_bridgers:
            u = users.get(n, {})
            writer.writerow([n, u.get("Users", ""), u.get("Party", ""), u.get("Chamber", ""), round(v, 6)])

    names = [users.get(n, {}).get("Users", str(n)) for n, _ in top_bridgers]
    vals = [v for _, v in top_bridgers]
    party_colors_bar = [("#1f77b4" if node_party.get(n) == "Democrat" else "#d62728") for n, _ in top_bridgers]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(names[::-1], vals[::-1], color=party_colors_bar[::-1])
    ax.set_xlabel("Cross-Party Out-Strength")
    ax.set_title("Top 20 Cross-Party Bridging Nodes\n(blue=Democrat, red=Republican)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "04_top_bridgers.png"), dpi=200)
    plt.close()

    print("Saved: results/cross_party_stats.csv, top_bridgers.csv")
    print("Saved: figures/04_cross_party_heatmap.png, 04_top_bridgers.png")


if __name__ == "__main__":
    main()
