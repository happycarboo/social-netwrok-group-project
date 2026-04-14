# -*- coding: utf-8 -*-
"""
RQ3 - Cross-Party Influence
Q3.1  To what extent are there cross-party influences?
Q3.2  Are there any critical bridging nodes that act as articulation points?
Q3.3  Is there a stronger influence within the same party?
"""

import csv
import json
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from utils import (load_graph, load_users, party_of, username_of,
                   PARTY_COLORS, PARTIES, FIG_DIR, RES_DIR, save_fig)


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())
    N = G.number_of_nodes()
    node_party = {n: party_of(users, n) for n in nodes}

    main_parties = ["Democrat", "Republican"]

    # =====================================================================
    # Q3.1 + Q3.3: Cross-party extent and within-party strength
    # =====================================================================
    print("=" * 60)
    print("Q3.1 + Q3.3: Within-party vs cross-party influence")
    print("=" * 60)

    # Party-to-party flow matrix (count and weight)
    flow_count = defaultdict(int)
    flow_weight = defaultdict(float)
    total_count = 0
    total_weight = 0.0

    for u, v, d in G.edges(data=True):
        sp = node_party[u]
        tp = node_party[v]
        w = d.get("weight", 0)
        flow_count[(sp, tp)] += 1
        flow_weight[(sp, tp)] += w
        total_count += 1
        total_weight += w

    # Within vs cross
    within_count = sum(flow_count[(p, p)] for p in PARTIES)
    cross_count = total_count - within_count
    within_weight = sum(flow_weight[(p, p)] for p in PARTIES)
    cross_weight = total_weight - within_weight

    print(f"  Within-party edges: {within_count} ({within_count/total_count*100:.1f}%)")
    print(f"  Cross-party edges:  {cross_count} ({cross_count/total_count*100:.1f}%)")
    print(f"  Within-party weight: {within_weight:.3f} ({within_weight/total_weight*100:.1f}%)")
    print(f"  Cross-party weight:  {cross_weight:.3f} ({cross_weight/total_weight*100:.1f}%)")

    # D-to-R vs R-to-D
    d2r_c = flow_count[("Democrat", "Republican")]
    r2d_c = flow_count[("Republican", "Democrat")]
    d2r_w = flow_weight[("Democrat", "Republican")]
    r2d_w = flow_weight[("Republican", "Democrat")]
    print(f"\n  Dem -> Rep: {d2r_c} edges, weight={d2r_w:.3f}")
    print(f"  Rep -> Dem: {r2d_c} edges, weight={r2d_w:.3f}")

    # Strong vs weak ties analysis (L6)
    all_weights = [d["weight"] for _, _, d in G.edges(data=True)]
    median_w = float(np.median(all_weights))
    print(f"\n  Median edge weight (strong/weak threshold): {median_w:.6f}")

    strong_within = 0
    strong_cross = 0
    weak_within = 0
    weak_cross = 0
    for u, v, d in G.edges(data=True):
        w = d["weight"]
        same = node_party[u] == node_party[v]
        if w > median_w:
            if same:
                strong_within += 1
            else:
                strong_cross += 1
        else:
            if same:
                weak_within += 1
            else:
                weak_cross += 1

    total_strong = strong_within + strong_cross
    total_weak = weak_within + weak_cross
    print(f"  Strong ties within-party: {strong_within} ({strong_within/total_strong*100:.1f}%)")
    print(f"  Strong ties cross-party:  {strong_cross} ({strong_cross/total_strong*100:.1f}%)")
    print(f"  Weak ties within-party:   {weak_within} ({weak_within/total_weak*100:.1f}%)")
    print(f"  Weak ties cross-party:    {weak_cross} ({weak_cross/total_weak*100:.1f}%)")

    homophily_data = {
        "within_party_edges": within_count,
        "cross_party_edges": cross_count,
        "within_party_pct": round(within_count / total_count * 100, 1),
        "within_party_weight_pct": round(within_weight / total_weight * 100, 1),
        "dem_to_rep_edges": d2r_c,
        "rep_to_dem_edges": r2d_c,
        "dem_to_rep_weight": round(d2r_w, 4),
        "rep_to_dem_weight": round(r2d_w, 4),
        "median_weight_threshold": round(median_w, 6),
        "strong_within_party_pct": round(strong_within / total_strong * 100, 1),
        "strong_cross_party_pct": round(strong_cross / total_strong * 100, 1),
    }
    with open(f"{RES_DIR}/rq3_homophily.json", "w") as f:
        json.dump(homophily_data, f, indent=2)

    # Save party-to-party matrix
    with open(f"{RES_DIR}/rq3_flow_matrix.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "edge_count", "total_weight"])
        for sp in PARTIES:
            for tp in PARTIES:
                w.writerow([sp, tp, flow_count[(sp, tp)],
                           round(flow_weight[(sp, tp)], 6)])

    # =====================================================================
    # Q3.2: Bridging nodes and articulation points
    # =====================================================================
    print("\n" + "=" * 60)
    print("Q3.2: Bridging nodes and articulation points")
    print("=" * 60)

    G_ud = G.to_undirected()
    art_points = list(nx.articulation_points(G_ud))
    print(f"  Articulation points: {len(art_points)}")

    # Cross-party betweenness: nodes with high betweenness AND cross-party edges
    betw = nx.betweenness_centrality(G, normalized=True)

    bridge_scores = []
    for n in nodes:
        cross_out_w = sum(
            d.get("weight", 0)
            for _, v, d in G.out_edges(n, data=True)
            if node_party[v] != node_party[n]
        )
        cross_in_w = sum(
            d.get("weight", 0)
            for u, _, d in G.in_edges(n, data=True)
            if node_party[u] != node_party[n]
        )
        cross_out_c = sum(
            1 for _, v in G.out_edges(n) if node_party[v] != node_party[n]
        )
        cross_in_c = sum(
            1 for u, _ in G.in_edges(n) if node_party[u] != node_party[n]
        )
        bridge_scores.append({
            "node_id": n,
            "username": username_of(users, n),
            "party": node_party[n],
            "betweenness": round(betw[n], 6),
            "cross_out_edges": cross_out_c,
            "cross_in_edges": cross_in_c,
            "cross_out_weight": round(cross_out_w, 6),
            "cross_in_weight": round(cross_in_w, 6),
            "total_cross_weight": round(cross_out_w + cross_in_w, 6),
        })

    bridge_scores.sort(key=lambda x: x["total_cross_weight"], reverse=True)

    with open(f"{RES_DIR}/rq3_bridge_scores.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bridge_scores[0].keys()))
        w.writeheader()
        w.writerows(bridge_scores)

    print("\n  Top 10 cross-party bridgers (by total cross-party weight):")
    for i, r in enumerate(bridge_scores[:10]):
        print(f"    {i+1:2d}. {r['username']:20s} {r['party']:12s} "
              f"cross_w={r['total_cross_weight']:.4f}  betw={r['betweenness']:.4f}")

    # =====================================================================
    # FIGURES - 2x2 grid
    # =====================================================================
    print("\nGenerating RQ3 figures...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # Panel A: Party-to-party flow heatmap (count)
    ax = axes[0, 0]
    count_mat = np.array([[flow_count[(p1, p2)] for p2 in main_parties] for p1 in main_parties])
    im = ax.imshow(count_mat, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(main_parties)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(main_parties)
    ax.set_xlabel("Target party")
    ax.set_ylabel("Source party")
    ax.set_title("(A) Party-to-Party Edge Count")
    for i in range(2):
        for j in range(2):
            pct = count_mat[i, j] / count_mat.sum() * 100
            ax.text(j, i, f"{count_mat[i,j]:,}\n({pct:.1f}%)",
                    ha="center", va="center", fontsize=10,
                    color="white" if count_mat[i, j] > count_mat.max() * 0.5 else "black")

    # Panel B: Within vs cross-party (count + weight)
    ax = axes[0, 1]
    categories = ["By Edge Count", "By Edge Weight"]
    within_vals = [within_count / total_count * 100, within_weight / total_weight * 100]
    cross_vals = [cross_count / total_count * 100, cross_weight / total_weight * 100]
    x = np.arange(len(categories))
    bw = 0.35
    b1 = ax.bar(x - bw / 2, within_vals, bw, label="Within-party", color="steelblue")
    b2 = ax.bar(x + bw / 2, cross_vals, bw, label="Cross-party", color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel("Percentage (%)")
    ax.set_title("(B) Homophily: Within vs Cross-Party")
    ax.legend(fontsize=8)
    for bar in b1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{bar.get_height():.1f}%", ha="center", fontsize=9)
    for bar in b2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{bar.get_height():.1f}%", ha="center", fontsize=9)

    # Panel C: Strong vs weak ties by party context
    ax = axes[1, 0]
    tie_cats = ["Strong\nWithin", "Strong\nCross", "Weak\nWithin", "Weak\nCross"]
    tie_vals = [strong_within, strong_cross, weak_within, weak_cross]
    tie_colors = ["steelblue", "tomato", "#7fb3d8", "#f0a0a0"]
    bars = ax.bar(tie_cats, tie_vals, color=tie_colors, edgecolor="white")
    ax.set_ylabel("Number of edges")
    ax.set_title("(C) Strong vs Weak Ties (L6)")
    for bar, v in zip(bars, tie_vals):
        pct = v / total_count * 100
        ax.text(bar.get_x() + bar.get_width() / 2, v + 50,
                f"{v:,}\n({pct:.1f}%)", ha="center", fontsize=8)

    # Panel D: Top 10 cross-party bridgers
    ax = axes[1, 1]
    top10 = bridge_scores[:10]
    names = [r["username"] for r in top10][::-1]
    vals = [r["total_cross_weight"] for r in top10][::-1]
    colors = [PARTY_COLORS[r["party"]] for r in top10][::-1]
    ax.barh(names, vals, color=colors, edgecolor="white")
    ax.set_xlabel("Total cross-party edge weight")
    ax.set_title("(D) Top 10 Cross-Party Bridgers")
    ax.tick_params(axis="y", labelsize=8)

    fig.suptitle("RQ3 - Cross-Party Influence", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "04_rq3_cross_party.png")

    print("\nDone: 04_rq3_cross_party.py")


if __name__ == "__main__":
    main()
