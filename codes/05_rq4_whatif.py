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
                   PARTY_COLORS, PARTIES, FIG_DIR, RES_DIR, save_fig)


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
    # FIGURES - 2x2 grid comparing key metrics across scenarios
    # =====================================================================
    print("\nGenerating RQ4 figures...")

    metrics_to_plot = [
        ("largest_scc_frac", "Largest SCC Fraction", "(A)"),
        ("avg_path_length", "Avg Path Length (SCC)", "(B)"),
        ("avg_clustering", "Avg Clustering Coefficient", "(C)"),
        ("density", "Network Density", "(D)"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for idx, (metric, label, panel) in enumerate(metrics_to_plot):
        ax = axes[idx // 2, idx % 2]

        # x-axis: removal counts
        x = np.arange(len(remove_counts))
        bw = 0.25

        baseline_val = baseline[metric]
        ax.axhline(y=baseline_val, color="gray", linestyle="--", alpha=0.6, label="Baseline")

        overall_vals = [scenarios[f"top_{k}_overall"][metric] for k in remove_counts]
        dem_vals = [scenarios[f"top_{k}_dem"][metric] for k in remove_counts]
        rep_vals = [scenarios[f"top_{k}_rep"][metric] for k in remove_counts]

        ax.bar(x - bw, overall_vals, bw, label="Remove top overall", color="#2ca02c")
        ax.bar(x, dem_vals, bw, label="Remove top Dem", color=PARTY_COLORS["Democrat"])
        ax.bar(x + bw, rep_vals, bw, label="Remove top Rep", color=PARTY_COLORS["Republican"])

        ax.set_xticks(x)
        ax.set_xticklabels([f"Top {k}" for k in remove_counts])
        ax.set_ylabel(label)
        ax.set_title(f"{panel} {label}")
        ax.legend(fontsize=7, loc="best")

    fig.suptitle("RQ4 - What-If: Removing Top Influencers",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "05_rq4_whatif.png")

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
