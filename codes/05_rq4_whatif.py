# -*- coding: utf-8 -*-
"""
RQ4 - What-If Analysis
What if we remove the top influencers? How does the network structure change?
Compare removing top Democrats vs top Republicans.
"""

import csv
import json

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from utils import (load_graph, load_users, party_of, username_of,
                   PARTY_COLORS, PARTIES, FIG_DIR, RES_DIR, save_fig,
                   CLR_DEM, CLR_REP, CLR_DEM_LIGHT, CLR_REP_LIGHT, CLR_NEUTRAL)


def network_stats(G):
    """Compute key structural metrics for a given graph."""
    N = G.number_of_nodes()
    M = G.number_of_edges()
    if N == 0:
        return {"nodes": 0, "edges": 0}

    density = nx.density(G)
    recip = nx.reciprocity(G) if M > 0 else 0
    n_scc = nx.number_strongly_connected_components(G)
    largest_scc = max(nx.strongly_connected_components(G), key=len)
    scc_frac = len(largest_scc) / N

    G_ud = G.to_undirected()
    avg_clust = nx.average_clustering(G_ud) if N > 2 else 0

    # Average path length on largest SCC
    scc_sub = G.subgraph(largest_scc)
    avg_path = nx.average_shortest_path_length(scc_sub) if len(largest_scc) > 1 else 0
    diameter = nx.diameter(scc_sub) if len(largest_scc) > 1 else 0

    return {
        "nodes": N,
        "edges": M,
        "density": round(density, 4),
        "reciprocity": round(recip, 4),
        "scc_count": n_scc,
        "largest_scc_frac": round(scc_frac, 4),
        "avg_clustering": round(avg_clust, 4),
        "avg_path_length": round(avg_path, 2),
        "diameter": diameter,
    }


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())
    node_party = {n: party_of(users, n) for n in nodes}

    # Load VC scores
    vc = {}
    with open(f"{RES_DIR}/viral_centrality_scores.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vc[int(row["node_id"])] = float(row["viral_centrality"])

    # Baseline stats
    baseline = network_stats(G)
    print("=" * 60)
    print("BASELINE NETWORK")
    print("=" * 60)
    for k, v in baseline.items():
        print(f"  {k}: {v}")

    # Sort nodes by VC
    vc_ranked = sorted(vc.items(), key=lambda x: x[1], reverse=True)

    # Scenarios
    remove_counts = [5, 10, 15]
    scenarios = {}

    # Scenario A: Remove top N overall
    print("\n" + "=" * 60)
    print("SCENARIO A: Remove top N influencers (by VC)")
    print("=" * 60)
    for k in remove_counts:
        to_remove = [n for n, _ in vc_ranked[:k]]
        removed_names = [username_of(users, n) for n in to_remove]
        G_rem = G.copy()
        G_rem.remove_nodes_from(to_remove)
        stats = network_stats(G_rem)
        scenarios[f"top_{k}_overall"] = stats
        print(f"\n  Remove top {k}: {', '.join(removed_names[:5])}{'...' if k > 5 else ''}")
        for key, val in stats.items():
            diff = ""
            if key in baseline and isinstance(val, (int, float)):
                bv = baseline[key]
                if bv != 0:
                    pct = (val - bv) / abs(bv) * 100
                    diff = f"  ({pct:+.1f}%)"
            print(f"    {key}: {val}{diff}")

    # Scenario B: Remove top N Democrats
    print("\n" + "=" * 60)
    print("SCENARIO B: Remove top N Democrat influencers")
    print("=" * 60)
    dem_ranked = [(n, s) for n, s in vc_ranked if node_party[n] == "Democrat"]
    for k in remove_counts:
        to_remove = [n for n, _ in dem_ranked[:k]]
        removed_names = [username_of(users, n) for n in to_remove]
        G_rem = G.copy()
        G_rem.remove_nodes_from(to_remove)
        stats = network_stats(G_rem)
        scenarios[f"top_{k}_dem"] = stats
        print(f"\n  Remove top {k} Dem: {', '.join(removed_names[:5])}{'...' if k > 5 else ''}")
        for key, val in stats.items():
            diff = ""
            if key in baseline and isinstance(val, (int, float)):
                bv = baseline[key]
                if bv != 0:
                    pct = (val - bv) / abs(bv) * 100
                    diff = f"  ({pct:+.1f}%)"
            print(f"    {key}: {val}{diff}")

    # Scenario C: Remove top N Republicans
    print("\n" + "=" * 60)
    print("SCENARIO C: Remove top N Republican influencers")
    print("=" * 60)
    rep_ranked = [(n, s) for n, s in vc_ranked if node_party[n] == "Republican"]
    for k in remove_counts:
        to_remove = [n for n, _ in rep_ranked[:k]]
        removed_names = [username_of(users, n) for n in to_remove]
        G_rem = G.copy()
        G_rem.remove_nodes_from(to_remove)
        stats = network_stats(G_rem)
        scenarios[f"top_{k}_rep"] = stats
        print(f"\n  Remove top {k} Rep: {', '.join(removed_names[:5])}{'...' if k > 5 else ''}")
        for key, val in stats.items():
            diff = ""
            if key in baseline and isinstance(val, (int, float)):
                bv = baseline[key]
                if bv != 0:
                    pct = (val - bv) / abs(bv) * 100
                    diff = f"  ({pct:+.1f}%)"
            print(f"    {key}: {val}{diff}")

    # Save all scenario data
    all_data = {"baseline": baseline, "scenarios": scenarios}
    with open(f"{RES_DIR}/rq4_whatif.json", "w") as f:
        json.dump(all_data, f, indent=2)

    # =====================================================================
    # FIGURES - % change from baseline (much easier to read)
    # =====================================================================
    print("\nGenerating RQ4 figures...")

    metrics_to_plot = [
        ("edges", "Edges"),
        ("density", "Density"),
        ("avg_clustering", "Avg Clustering"),
        ("avg_path_length", "Avg Path Length"),
        ("largest_scc_frac", "Largest SCC Frac."),
        ("reciprocity", "Reciprocity"),
    ]

    def pct_change(val, base):
        return (val - base) / abs(base) * 100 if base != 0 else 0

    # --- Figure 1: Grouped bar chart of % change ---
    fig, ax = plt.subplots(figsize=(13, 6))

    n_metrics = len(metrics_to_plot)
    x = np.arange(n_metrics)
    bw = 0.12
    groups = [
        ("top_5_overall",  "Remove top 5 overall",  CLR_NEUTRAL, -2.5),
        ("top_5_dem",      "Remove top 5 Dem",       CLR_DEM, -1.5),
        ("top_5_rep",      "Remove top 5 Rep",       CLR_REP, -0.5),
        ("top_15_overall", "Remove top 15 overall",  "#b0b0b0", 0.5),
        ("top_15_dem",     "Remove top 15 Dem",      CLR_DEM_LIGHT, 1.5),
        ("top_15_rep",     "Remove top 15 Rep",      CLR_REP_LIGHT, 2.5),
    ]

    for key, label, color, offset in groups:
        vals = [pct_change(scenarios[key][m], baseline[m]) for m, _ in metrics_to_plot]
        bars = ax.bar(x + offset * bw, vals, bw, label=label, color=color, edgecolor="white")
        for bar, v in zip(bars, vals):
            if abs(v) > 0.3:
                ax.text(bar.get_x() + bar.get_width() / 2, v + (0.15 if v >= 0 else -0.4),
                        f"{v:.1f}%", ha="center", fontsize=6.5, rotation=0)

    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, lab in metrics_to_plot], fontsize=9)
    ax.set_ylabel("% Change from Baseline")
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.legend(fontsize=7, ncol=3, loc="lower left")
    ax.set_title("RQ4 - What-If: % Change After Removing Top Influencers",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "05_rq4_whatif.png")

    # --- Figure 2: Dem vs Rep comparison at each removal level ---
    fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for i, k in enumerate(remove_counts):
        ax = axes2[i]
        dem_pcts = [pct_change(scenarios[f"top_{k}_dem"][m], baseline[m])
                    for m, _ in metrics_to_plot]
        rep_pcts = [pct_change(scenarios[f"top_{k}_rep"][m], baseline[m])
                    for m, _ in metrics_to_plot]
        y = np.arange(n_metrics)
        ax.barh(y - 0.2, dem_pcts, 0.35, label="Remove Dem", color=PARTY_COLORS["Democrat"])
        ax.barh(y + 0.2, rep_pcts, 0.35, label="Remove Rep", color=PARTY_COLORS["Republican"])
        ax.set_yticks(y)
        ax.set_yticklabels([lab for _, lab in metrics_to_plot], fontsize=9)
        ax.axvline(x=0, color="black", linewidth=0.8)
        ax.set_xlabel("% Change")
        ax.set_title(f"Remove Top {k}")
        ax.legend(fontsize=8)

    fig2.suptitle("RQ4 - Democrat vs Republican Removal Impact",
                  fontsize=13, fontweight="bold", y=1.02)
    fig2.tight_layout()
    save_fig(fig2, "05_rq4_whatif_comparison.png")

    # Names of removed nodes for the report
    print("\n  Removed nodes (for reference):")
    for k in remove_counts:
        top_overall = [username_of(users, n) for n, _ in vc_ranked[:k]]
        top_dem = [username_of(users, n) for n, _ in dem_ranked[:k]]
        top_rep = [username_of(users, n) for n, _ in rep_ranked[:k]]
        print(f"    Top {k} overall: {', '.join(top_overall)}")
        print(f"    Top {k} Dem:     {', '.join(top_dem)}")
        print(f"    Top {k} Rep:     {', '.join(top_rep)}")

    print("\nDone: 05_rq4_whatif.py")


if __name__ == "__main__":
    main()
