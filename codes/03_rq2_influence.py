# -*- coding: utf-8 -*-
"""
RQ2 - Focus on Influence
Q2.1  Who are the most influential users, and why?
Q2.2  Is there an imbalance of influence where influence is not reciprocated?
Q2.3  Are the influential users balanced across parties?
"""

import csv
import json
import sys
import os
from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (load_graph, load_users, party_of, username_of,
                   PARTY_COLORS, PARTIES, FIG_DIR, RES_DIR, save_fig)


def compute_viral_centrality():
    """Run VC from dataset JSON if not already cached."""
    vc_path = os.path.join(RES_DIR, "viral_centrality_scores.csv")
    if os.path.exists(vc_path):
        print("  VC scores already computed, loading from cache.")
        scores = {}
        with open(vc_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores[int(row["node_id"])] = float(row["viral_centrality"])
        return scores

    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "congress_network")
    import json as _json
    from viral_centrality import viral_centrality

    with open(os.path.join(DATA_DIR, "congress_network_data.json"), encoding="utf-8") as f:
        data = _json.load(f)[0]

    num_activated = viral_centrality(
        data["inList"], data["inWeight"], data["outList"], Niter=-1, tol=0.001
    )
    scores = {i: float(v) for i, v in enumerate(num_activated)}
    username_list = data["usernameList"]

    with open(vc_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node_id", "username", "viral_centrality"])
        for i in range(len(num_activated)):
            w.writerow([i, username_list[i], round(float(num_activated[i]), 6)])
    print(f"  VC scores computed and saved.")
    return scores


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())
    N = G.number_of_nodes()

    # =====================================================================
    # Q2.1  Most influential users
    # =====================================================================
    print("=" * 60)
    print("Q2.1: Most influential users")
    print("=" * 60)

    out_deg = dict(G.out_degree())
    in_deg = dict(G.in_degree())
    out_str = {n: sum(d for _, _, d in G.out_edges(n, data="weight", default=0)) for n in nodes}
    in_str = {n: sum(d for _, _, d in G.in_edges(n, data="weight", default=0)) for n in nodes}
    betw = nx.betweenness_centrality(G, normalized=True)
    close = nx.closeness_centrality(G)
    try:
        eigen = nx.eigenvector_centrality(G, weight="weight", max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        eigen = nx.eigenvector_centrality(G, max_iter=1000)

    print("  Computing Viral Centrality...")
    vc = compute_viral_centrality()

    # Build full table
    rows = []
    for n in nodes:
        rows.append({
            "node_id": n,
            "username": username_of(users, n),
            "party": party_of(users, n),
            "out_degree": out_deg[n],
            "in_degree": in_deg[n],
            "out_strength": round(out_str.get(n, 0), 6),
            "in_strength": round(in_str.get(n, 0), 6),
            "betweenness": round(betw.get(n, 0), 6),
            "closeness": round(close.get(n, 0), 6),
            "eigenvector": round(eigen.get(n, 0), 6),
            "viral_centrality": round(vc.get(n, 0), 6),
        })
    rows.sort(key=lambda x: x["viral_centrality"], reverse=True)

    with open(f"{RES_DIR}/rq2_centrality_full.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("\n  Top 10 by Viral Centrality:")
    for i, r in enumerate(rows[:10]):
        print(f"    {i+1:2d}. {r['username']:20s} {r['party']:12s} VC={r['viral_centrality']:.3f}"
              f"  Betw={r['betweenness']:.4f}  Out-Str={r['out_strength']:.3f}")

    # =====================================================================
    # Q2.2  Influence imbalance / reciprocity
    # =====================================================================
    print("\n" + "=" * 60)
    print("Q2.2: Influence imbalance")
    print("=" * 60)

    recip = nx.reciprocity(G)
    print(f"  Network reciprocity: {recip:.4f}")

    # Categorise nodes: broadcaster (high out, low in) vs receiver (high in, low out)
    out_str_arr = np.array([out_str[n] for n in nodes])
    in_str_arr = np.array([in_str[n] for n in nodes])
    ratio = out_str_arr / np.maximum(in_str_arr, 1e-9)
    median_ratio = np.median(ratio)
    print(f"  Median out/in strength ratio: {median_ratio:.3f}")

    # Correlation between out-strength and in-strength
    corr = np.corrcoef(out_str_arr, in_str_arr)[0, 1]
    print(f"  Correlation(out-strength, in-strength): {corr:.4f}")

    imbalance_data = {
        "reciprocity": round(recip, 4),
        "median_out_in_ratio": round(median_ratio, 3),
        "out_in_correlation": round(corr, 4),
    }
    with open(f"{RES_DIR}/rq2_imbalance.json", "w") as f:
        json.dump(imbalance_data, f, indent=2)

    # =====================================================================
    # Q2.3  Party balance among top influencers
    # =====================================================================
    print("\n" + "=" * 60)
    print("Q2.3: Party balance in top influencers")
    print("=" * 60)

    top_ns = [10, 20, 50]
    balance = {}
    for top_n in top_ns:
        top = rows[:top_n]
        party_cnt = Counter(r["party"] for r in top)
        balance[f"top_{top_n}"] = {p: party_cnt.get(p, 0) for p in PARTIES}
        print(f"  Top {top_n} by VC: " +
              ", ".join(f"{p}={party_cnt.get(p,0)}" for p in PARTIES))

    with open(f"{RES_DIR}/rq2_party_balance.json", "w") as f:
        json.dump(balance, f, indent=2)

    # =====================================================================
    # FIGURES - 2x2 grid
    # =====================================================================
    print("\nGenerating RQ2 figures...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # Panel A: Top 15 by Viral Centrality
    ax = axes[0, 0]
    top15 = rows[:15]
    names = [r["username"] for r in top15][::-1]
    vals = [r["viral_centrality"] for r in top15][::-1]
    colors = [PARTY_COLORS[r["party"]] for r in top15][::-1]
    ax.barh(names, vals, color=colors, edgecolor="white")
    ax.set_xlabel("Viral Centrality")
    ax.set_title("(A) Top 15 by Viral Centrality")
    ax.tick_params(axis="y", labelsize=8)

    # Panel B: Out-strength vs In-strength scatter
    ax = axes[0, 1]
    for p in PARTIES:
        mask = [party_of(users, n) == p for n in nodes]
        ax.scatter(
            out_str_arr[mask], in_str_arr[mask],
            c=PARTY_COLORS[p], label=p, alpha=0.5, s=15, edgecolors="none"
        )
    ax.plot([0, max(out_str_arr)], [0, max(out_str_arr)],
            "k--", alpha=0.3, linewidth=0.8)
    ax.set_xlabel("Out-strength (broadcasting)")
    ax.set_ylabel("In-strength (receiving)")
    ax.set_title(f"(B) Influence Imbalance (r={corr:.2f})")
    ax.legend(fontsize=8)

    # Panel C: Top 15 by Betweenness
    ax = axes[1, 0]
    betw_sorted = sorted(rows, key=lambda x: x["betweenness"], reverse=True)[:15]
    names_b = [r["username"] for r in betw_sorted][::-1]
    vals_b = [r["betweenness"] for r in betw_sorted][::-1]
    colors_b = [PARTY_COLORS[r["party"]] for r in betw_sorted][::-1]
    ax.barh(names_b, vals_b, color=colors_b, edgecolor="white")
    ax.set_xlabel("Betweenness Centrality")
    ax.set_title("(B) Top 15 by Betweenness (Brokerage)")
    ax.tick_params(axis="y", labelsize=8)

    # Panel D: Party balance in top N
    ax = axes[1, 1]
    x_pos = np.arange(len(top_ns))
    bw = 0.25
    for i, p in enumerate(["Democrat", "Republican"]):
        vals_p = [balance[f"top_{n}"].get(p, 0) for n in top_ns]
        ax.bar(x_pos + i * bw, vals_p, bw, label=p, color=PARTY_COLORS[p])
    ax.set_xticks(x_pos + bw / 2)
    ax.set_xticklabels([f"Top {n}" for n in top_ns])
    ax.set_ylabel("Number of members")
    ax.set_title("(D) Party Representation Among Top Influencers")
    ax.legend(fontsize=8)
    # Baseline reference lines
    for n_top in top_ns:
        expected_dem = n_top * 205 / 475
        expected_rep = n_top * 178 / 475

    fig.suptitle("RQ2 - Focus on Influence", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "03_rq2_influence.png")

    print("\nDone: 03_rq2_influence.py")


if __name__ == "__main__":
    main()
