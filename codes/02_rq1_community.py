"""
RQ1 - Community Differences
Q1.1  How can the users be categorised?
Q1.2  How do the categories differ from one another?
Q1.3  Is the network structurally centralised around a few dominant members?
Q1.4  Does it exhibit high degree centralisation or betweenness centralisation?
"""

import csv
import json
from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib import cm

from utils import (load_graph, load_users, party_of, username_of,
                   PARTY_COLORS, PARTIES, FIG_DIR, RES_DIR, save_fig,
                   CLR_DEM, CLR_REP, CLR_NEUTRAL, CLR_DEM_LIGHT, CLR_REP_LIGHT)


def load_layout():
    d = np.load(f"{RES_DIR}/layout.npz", allow_pickle=True)
    nodes = d["nodes"]
    return {int(n): (x, y) for n, x, y in zip(nodes, d["x"], d["y"])}


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())
    N = G.number_of_nodes()
    G_ud = G.to_undirected()
    pos = load_layout()

    # =====================================================================
    # Q1.1 + Q1.2  Categorisation and community differences
    # =====================================================================
    print("=" * 60)
    print("Q1.1-1.2: Categorisation by party & community differences")
    print("=" * 60)

    communities = {p: [n for n in nodes if party_of(users, n) == p] for p in PARTIES}

    # --- Internal vs external density (edge-count based) ---
    density_results = []
    for name, members in communities.items():
        comm = set(members)
        n_c = len(comm)
        n_out = N - n_c
        if n_c < 2:
            continue

        int_edges = sum(1 for u, v in G.edges() if u in comm and v in comm)
        max_int = n_c * (n_c - 1)  # directed
        int_density = int_edges / max_int if max_int else 0

        ext_edges = sum(1 for u, v in G.edges() if (u in comm) != (v in comm))
        max_ext = 2 * n_c * n_out  # directed both ways
        ext_density = ext_edges / max_ext if max_ext else 0

        ratio = int_density / ext_density if ext_density else float("inf")
        density_results.append({
            "community": name,
            "size": n_c,
            "internal_edges": int_edges,
            "internal_density": round(int_density, 4),
            "external_edges": ext_edges,
            "external_density": round(ext_density, 4),
            "ratio": round(ratio, 1),
            "cohesive": int_density > ext_density,
        })
        label = "COHESIVE" if int_density > ext_density else "NOT COHESIVE"
        print(f"  {name:12s}: int_den={int_density:.4f}  ext_den={ext_density:.4f}"
              f"  ratio={ratio:.1f}x  ? {label}")

    with open(f"{RES_DIR}/rq1_density.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(density_results[0].keys()))
        w.writeheader()
        w.writerows(density_results)

    # --- Per-community stats ---
    print("\n  Per-community statistics:")
    comm_stats = []
    for name, members in communities.items():
        sub_d = G.subgraph(members)
        sub_u = G_ud.subgraph(members)
        n_c = len(members)
        m_c = sub_d.number_of_edges()
        avg_deg = (2 * m_c) / n_c if n_c else 0
        avg_clust = nx.average_clustering(sub_u) if n_c > 2 else 0
        avg_w = sum(d["weight"] for _, _, d in sub_d.edges(data=True)) / m_c if m_c else 0
        recip = nx.reciprocity(sub_d) if m_c > 0 else 0
        row = {
            "community": name, "nodes": n_c, "edges": m_c,
            "avg_degree": round(avg_deg, 2),
            "avg_clustering": round(avg_clust, 4),
            "avg_edge_weight": round(avg_w, 6),
            "reciprocity": round(recip, 4),
        }
        comm_stats.append(row)
        print(f"    {name:12s}: n={n_c}, edges={m_c}, avg_deg={avg_deg:.1f}, "
              f"clust={avg_clust:.3f}, avg_w={avg_w:.5f}, recip={recip:.3f}")

    with open(f"{RES_DIR}/rq1_community_stats.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comm_stats[0].keys()))
        w.writeheader()
        w.writerows(comm_stats)

    # --- K-core decomposition ---
    print("\n  K-core decomposition:")
    core_numbers = nx.core_number(G_ud)
    max_core = max(core_numbers.values())
    inner_core = [n for n, k in core_numbers.items() if k == max_core]
    print(f"    Max k-core: k={max_core}, inner core size: {len(inner_core)}")

    inner_party = Counter(party_of(users, n) for n in inner_core)
    for p in PARTIES:
        cnt = inner_party.get(p, 0)
        pct_core = cnt / len(inner_core) * 100
        pct_net = communities[p].__len__() / N * 100
        print(f"    {p:12s}: {cnt} in core ({pct_core:.1f}%) vs {pct_net:.1f}% of network")

    kcore_summary = {
        "max_k": max_core,
        "inner_core_size": len(inner_core),
        "party_composition": {p: inner_party.get(p, 0) for p in PARTIES},
    }
    with open(f"{RES_DIR}/rq1_kcore.json", "w") as f:
        json.dump(kcore_summary, f, indent=2)

    # =====================================================================
    # Q1.3 + Q1.4  Centralisation
    # =====================================================================
    print("\n" + "=" * 60)
    print("Q1.3-1.4: Network centralisation (Freeman)")
    print("=" * 60)

    in_deg = dict(G.in_degree())
    out_deg = dict(G.out_degree())
    betw = nx.betweenness_centrality(G, normalized=True)

    max_in = max(in_deg.values())
    max_out = max(out_deg.values())
    max_betw = max(betw.values())

    # Freeman centralisation: sum(C_max - C_i) / theoretical_max
    in_cent = sum(max_in - v for v in in_deg.values()) / ((N - 1) * (N - 1))
    out_cent = sum(max_out - v for v in out_deg.values()) / ((N - 1) * (N - 1))
    betw_cent = sum(max_betw - v for v in betw.values()) / (N - 1)

    print(f"  In-degree centralisation:  {in_cent:.4f}")
    print(f"  Out-degree centralisation: {out_cent:.4f}")
    print(f"  Betweenness centralisation: {betw_cent:.4f}")

    cent_data = {
        "in_degree_centralisation": round(in_cent, 4),
        "out_degree_centralisation": round(out_cent, 4),
        "betweenness_centralisation": round(betw_cent, 4),
        "max_in_degree_node": username_of(users, max(in_deg, key=in_deg.get)),
        "max_out_degree_node": username_of(users, max(out_deg, key=out_deg.get)),
        "max_betweenness_node": username_of(users, max(betw, key=betw.get)),
    }
    with open(f"{RES_DIR}/rq1_centralisation.json", "w") as f:
        json.dump(cent_data, f, indent=2)

    # =====================================================================
    # FIGURES - 2-2 grid
    # =====================================================================
    print("\nGenerating RQ1 figures...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # Panel A: Internal vs external density
    ax = axes[0, 0]
    x = np.arange(len(density_results))
    w_bar = 0.35
    ax.bar(x - w_bar / 2, [r["internal_density"] for r in density_results],
           w_bar, label="Internal density", color=CLR_DEM)
    ax.bar(x + w_bar / 2, [r["external_density"] for r in density_results],
           w_bar, label="External density", color=CLR_REP)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['community']}\n(n={r['size']})" for r in density_results])
    ax.set_ylabel("Edge density (directed)")
    ax.set_title("(A) Cohesion Test: Internal vs External Density")
    ax.legend(fontsize=8)
    for i, r in enumerate(density_results):
        ax.text(i, max(r["internal_density"], r["external_density"]) + 0.003,
                f"{r['ratio']}-", ha="center", fontsize=9, fontweight="bold")

    # Panel B: Per-community comparison
    ax = axes[0, 1]
    metrics = ["avg_degree", "avg_clustering", "reciprocity"]
    labels_m = ["Avg Degree\n(-10)", "Avg Clustering\nCoeff.", "Reciprocity"]
    x2 = np.arange(len(metrics))
    bw = 0.25
    for i, s in enumerate(comm_stats):
        vals = [s["avg_degree"] / 10, s["avg_clustering"], s["reciprocity"]]
        ax.bar(x2 + i * bw, vals, bw, label=s["community"],
               color=PARTY_COLORS[s["community"]])
    ax.set_xticks(x2 + bw)
    ax.set_xticklabels(labels_m, fontsize=8)
    ax.set_title("(B) Community Profile Comparison")
    ax.legend(fontsize=8)

    # Panel C: K-core party composition
    ax = axes[1, 0]
    core_dist = Counter(core_numbers.values())
    ks = sorted(core_dist.keys())
    ax.bar(ks, [core_dist[k] for k in ks], color=CLR_NEUTRAL, edgecolor="white")
    ax.set_xlabel("K-core number")
    ax.set_ylabel("Number of nodes")
    ax.set_title(f"(C) K-core Distribution (inner core k={max_core})")
    ax.axvline(x=max_core, color="red", linestyle="--", alpha=0.7)
    ax.text(max_core + 0.3, max(core_dist.values()) * 0.8,
            f"k={max_core}", color="red", fontsize=9)

    # Panel D: Centralisation comparison
    ax = axes[1, 1]
    cent_labels = ["In-Degree", "Out-Degree", "Betweenness"]
    cent_vals = [in_cent, out_cent, betw_cent]
    colors = [CLR_DEM, CLR_REP, CLR_NEUTRAL]
    bars = ax.bar(cent_labels, cent_vals, color=colors, width=0.5)
    ax.set_ylabel("Freeman Centralisation Index")
    ax.set_title("(D) Network Centralisation (Freeman)")
    ax.set_ylim(0, max(cent_vals) * 1.3)
    for bar, v in zip(bars, cent_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.002,
                f"{v:.4f}", ha="center", fontsize=9)

    fig.suptitle("RQ1 - Community Differences", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "02_rq1_community.png")

    # --- Supplementary: K-core inner core party pie ---
    fig2, axes2 = plt.subplots(1, 2, figsize=(11, 4.5))

    ax = axes2[0]
    pie_labels = [f"{p}\n({inner_party.get(p,0)})" for p in PARTIES if inner_party.get(p, 0) > 0]
    pie_vals = [inner_party.get(p, 0) for p in PARTIES if inner_party.get(p, 0) > 0]
    pie_colors = [PARTY_COLORS[p] for p in PARTIES if inner_party.get(p, 0) > 0]
    ax.pie(pie_vals, labels=pie_labels, colors=pie_colors, autopct="%1.1f%%",
           startangle=90, textprops={"fontsize": 9})
    ax.set_title(f"(A) Inner Core (k={max_core}) Party Composition")

    ax = axes2[1]
    full_labels = [f"{p}\n({len(communities[p])})" for p in PARTIES]
    full_vals = [len(communities[p]) for p in PARTIES]
    full_colors = [PARTY_COLORS[p] for p in PARTIES]
    ax.pie(full_vals, labels=full_labels, colors=full_colors, autopct="%1.1f%%",
           startangle=90, textprops={"fontsize": 9})
    ax.set_title("(B) Full Network Party Composition")

    fig2.suptitle("K-core Inner Core vs Full Network", fontsize=12, fontweight="bold")
    fig2.tight_layout()
    save_fig(fig2, "02_rq1_kcore_party.png")

    print("\nDone: 02_rq1_community.py")


if __name__ == "__main__":
    main()
