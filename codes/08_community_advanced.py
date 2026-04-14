"""
Advanced community structure analysis grounded in course lectures L4, L5, L6.

L4  — Strong vs Weak communities (internal vs external density)
L5  — K-core decomposition, F-Measure
L6  — Transitivity, Triadic closure, Strong Triadic Closure Property,
        Bridge, Gatekeeper nodes, Homophily (within-party ratio)
"""

import ast
import csv
import json
import os
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import networkx as nx
import numpy as np
from networkx.algorithms.community import greedy_modularity_communities

CODES_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CODES_DIR, "..", "congress_network")
FIG_DIR = os.path.join(CODES_DIR, "figures")
RES_DIR = os.path.join(CODES_DIR, "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

PARTY_COLORS = {"Democrat": "#1f77b4", "Republican": "#d62728"}


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────

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
    return {int(r[0]): dict(zip(header, r)) for r in rows[1:]}


# ─────────────────────────────────────────────────────────────────────────────
# L5 — K-core decomposition
# ─────────────────────────────────────────────────────────────────────────────

def analyse_kcore(G, users, pos):
    print("\n[L5] K-core decomposition...")
    G_ud = G.to_undirected()
    core_numbers = nx.core_number(G_ud)

    with open(os.path.join(RES_DIR, "kcore_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "username", "party", "chamber", "core_number"])
        for n, k in sorted(core_numbers.items(), key=lambda x: -x[1]):
            u = users.get(n, {})
            writer.writerow([n, u.get("Users", ""), u.get("Party", ""), u.get("Chamber", ""), k])

    max_core = max(core_numbers.values())
    nodes = list(G.nodes())
    core_vals = np.array([core_numbers[n] for n in nodes])

    dist = Counter(core_numbers.values())
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(dist.keys(), dist.values(), color="steelblue", edgecolor="white")
    ax.set_xlabel("K-core number")
    ax.set_ylabel("Number of nodes")
    ax.set_title("K-core Number Distribution")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "08_kcore_distribution.png"), dpi=200)
    plt.close()

    norm = plt.Normalize(vmin=core_vals.min(), vmax=core_vals.max())
    colors = [cm.plasma(norm(core_numbers[n])) for n in nodes]
    sizes = [10 + 80 * ((core_numbers[n] - core_vals.min()) / max(core_vals.max() - core_vals.min(), 1)) for n in nodes]

    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, alpha=0.02, width=0.25, edge_color="gray", arrows=False, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.9, ax=ax)
    sm = plt.cm.ScalarMappable(cmap=cm.plasma, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="K-core number", shrink=0.6)
    ax.set_title(f"K-core Decomposition — Inner Core k={max_core}", fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "08_kcore_network.png"), dpi=200)
    plt.close()

    inner_core = {n: k for n, k in core_numbers.items() if k == max_core}
    print(f"  Max k-core: {max_core}, inner core size: {len(inner_core)}")
    print(f"  Sample inner-core: {[users.get(n,{}).get('Users','?') for n in list(inner_core.keys())[:8]]}")
    return core_numbers, max_core


# ─────────────────────────────────────────────────────────────────────────────
# L4 — Strong vs Weak community test
# ─────────────────────────────────────────────────────────────────────────────

def analyse_community_strength(G, users):
    print("\n[L4] Strong vs Weak community analysis...")
    G_ud = G.to_undirected()
    # Use greedy modularity here only as the base partition for the L4 strength test
    # (community detection itself done by Girvan-Newman in 03_community.py)
    communities = list(greedy_modularity_communities(G_ud, weight="weight"))
    communities.sort(key=len, reverse=True)

    results = []
    for i, comm in enumerate(communities):
        comm = set(comm)
        subgraph = G_ud.subgraph(comm)
        n = len(comm)
        if n < 2:
            continue
        internal_edges = subgraph.number_of_edges()
        max_internal = n * (n - 1) / 2
        internal_density = internal_edges / max_internal if max_internal > 0 else 0

        external_edges = sum(1 for u, v in G_ud.edges() if (u in comm) != (v in comm))
        n_out = len(G.nodes()) - n
        max_external = n * n_out
        external_density = external_edges / max_external if max_external > 0 else 0

        is_strong = internal_density > external_density
        party_counts = Counter(users.get(nd, {}).get("Party", "Unknown") for nd in comm)
        dominant = party_counts.most_common(1)[0][0] if party_counts else ""

        results.append({
            "community_id": i,
            "size": n,
            "internal_edges": internal_edges,
            "internal_density": round(internal_density, 4),
            "external_edges": external_edges,
            "external_density": round(external_density, 4),
            "strong_community": is_strong,
            "dominant_party": dominant,
            "n_democrat": party_counts.get("Democrat", 0),
            "n_republican": party_counts.get("Republican", 0),
        })

    with open(os.path.join(RES_DIR, "community_strength.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    for r in results:
        label = "STRONG" if r["strong_community"] else "WEAK"
        print(f"  Community {r['community_id']} (n={r['size']}): "
              f"int={r['internal_density']:.4f} ext={r['external_density']:.4f} → {label} [{r['dominant_party']}]")

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(results))
    w = 0.35
    ax.bar(x - w/2, [r["internal_density"] for r in results], w, label="Internal density", color="steelblue")
    ax.bar(x + w/2, [r["external_density"] for r in results], w, label="External density", color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels([f"C{r['community_id']}\nn={r['size']}" for r in results])
    ax.set_ylabel("Edge density")
    ax.set_title("Community Strength Test: Internal vs External Density")
    ax.legend()
    for i, r in enumerate(results):
        label = "★Strong" if r["strong_community"] else "Weak"
        ax.text(i, max(r["internal_density"], r["external_density"]) + 0.002, label,
                ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "08_community_strength.png"), dpi=200)
    plt.close()
    return results


# ─────────────────────────────────────────────────────────────────────────────
# L5 — F-Measure (fragmentation)
# ─────────────────────────────────────────────────────────────────────────────

def analyse_fmeasure(G):
    print("\n[L5] F-Measure (fragmentation)...")
    G_ud = G.to_undirected()
    comps = list(nx.connected_components(G_ud))
    N = G.number_of_nodes()
    numer = sum(len(c) * (len(c) - 1) for c in comps)
    denom = N * (N - 1)
    f_measure = 1 - numer / denom if denom > 0 else 1.0
    print(f"  F-Measure: {f_measure:.6f}  (0 = fully connected, 1 = fully fragmented)")
    return f_measure


# ─────────────────────────────────────────────────────────────────────────────
# L6 — Homophily: within-party ratio
# ─────────────────────────────────────────────────────────────────────────────

def analyse_homophily(G, users):
    print("\n[L6] Homophily — within-party / cross-party edge ratio...")
    node_party = {n: users.get(n, {}).get("Party", None) for n in G.nodes()}

    internal = sum(1 for u, v in G.edges()
                   if node_party.get(u) and node_party.get(v) and node_party[u] == node_party[v])
    external = sum(1 for u, v in G.edges()
                   if node_party.get(u) and node_party.get(v) and node_party[u] != node_party[v])
    total = internal + external

    pct_within = internal / total * 100 if total > 0 else 0
    pct_cross = external / total * 100 if total > 0 else 0

    print(f"  Within-party edges: {internal} ({pct_within:.1f}%)")
    print(f"  Cross-party edges:  {external} ({pct_cross:.1f}%)")
    print(f"  Homophily interpretation (L6): strong — {pct_within:.0f}% of influence stays within party")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(["Within-party", "Cross-party"], [pct_within, pct_cross],
           color=["steelblue", "tomato"], edgecolor="white", width=0.5)
    ax.set_ylabel("% of edges")
    ax.set_title("Within-party vs Cross-party Influence")
    for i, v in enumerate([pct_within, pct_cross]):
        ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "08_homophily_bar.png"), dpi=200)
    plt.close()
    return pct_within, pct_cross


# ─────────────────────────────────────────────────────────────────────────────
# L6 — Transitivity and Triadic closure
# ─────────────────────────────────────────────────────────────────────────────

def analyse_transitivity(G):
    print("\n[L6] Transitivity and triadic closure...")
    G_ud = G.to_undirected()
    global_transitivity = nx.transitivity(G_ud)
    avg_clustering = nx.average_clustering(G_ud)
    triangles = sum(nx.triangles(G_ud).values()) // 3
    triples = sum(d * (d - 1) / 2 for _, d in G_ud.degree())
    print(f"  Global transitivity: {global_transitivity:.4f}")
    print(f"  Avg local clustering: {avg_clustering:.4f}")
    print(f"  Triangles: {triangles:,}  Connected triples: {int(triples):,}")
    return global_transitivity, avg_clustering, triangles, int(triples)


# ─────────────────────────────────────────────────────────────────────────────
# L6 — Strong Triadic Closure Property
# Classify ties as strong (weight > median) vs weak (≤ median).
# Strong Triadic Closure: if A has STRONG ties to B and C, then B and C
# should be connected (the property is violated if they are not).
# ─────────────────────────────────────────────────────────────────────────────

def analyse_strong_triadic_closure(G, users):
    print("\n[L6] Strong Triadic Closure Property (STC)...")
    G_ud = G.to_undirected()
    all_weights = [d for _, _, d in G_ud.edges(data="weight", default=0) if d > 0]
    median_w = float(np.median(all_weights))
    print(f"  Median edge weight (threshold): {median_w:.5f}")

    strong_edges = {(u, v) for u, v, d in G_ud.edges(data="weight", default=0) if d > median_w}
    weak_edges = {(u, v) for u, v, d in G_ud.edges(data="weight", default=0) if d <= median_w}

    print(f"  Strong ties (weight > median): {len(strong_edges)}")
    print(f"  Weak ties (weight ≤ median): {len(weak_edges)}")

    # Check STC violations: A-B strong AND A-C strong, but B-C missing
    strong_neighbors = defaultdict(set)
    for u, v in strong_edges:
        strong_neighbors[u].add(v)
        strong_neighbors[v].add(u)

    violations = 0
    total_tests = 0
    for a in G_ud.nodes():
        sn = list(strong_neighbors[a])
        for i in range(len(sn)):
            for j in range(i + 1, len(sn)):
                b, c = sn[i], sn[j]
                total_tests += 1
                if not G_ud.has_edge(b, c):
                    violations += 1

    violation_rate = violations / total_tests if total_tests > 0 else 0
    print(f"  STC tests (pairs of strong-tie neighbors): {total_tests:,}")
    print(f"  STC violations (B-C edge missing):         {violations:,} ({violation_rate*100:.1f}%)")
    print(f"  STC satisfaction rate: {(1-violation_rate)*100:.1f}%")

    # Party-wise STC analysis
    node_party = {n: users.get(n, {}).get("Party", None) for n in G.nodes()}
    same_party_strong = sum(1 for u, v in strong_edges
                            if node_party.get(u) and node_party.get(v) and node_party[u] == node_party[v])
    cross_party_strong = sum(1 for u, v in strong_edges
                             if node_party.get(u) and node_party.get(v) and node_party[u] != node_party[v])
    print(f"  Strong ties within-party: {same_party_strong} ({same_party_strong/len(strong_edges)*100:.1f}%)")
    print(f"  Strong ties cross-party:  {cross_party_strong} ({cross_party_strong/len(strong_edges)*100:.1f}%)")

    # Figure: tie strength breakdown
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].bar(["Strong ties\n(weight > median)", "Weak ties\n(weight ≤ median)"],
                [len(strong_edges), len(weak_edges)],
                color=["steelblue", "lightgray"], edgecolor="white")
    axes[0].set_ylabel("Number of ties")
    axes[0].set_title("Strong vs Weak Ties (L6)")
    for i, v in enumerate([len(strong_edges), len(weak_edges)]):
        axes[0].text(i, v + 30, str(v), ha="center", fontsize=11)

    axes[1].bar(["Within-party\nstrong ties", "Cross-party\nstrong ties"],
                [same_party_strong, cross_party_strong],
                color=["steelblue", "tomato"], edgecolor="white")
    axes[1].set_ylabel("Number of strong ties")
    axes[1].set_title("Strong Tie Homophily (L6)")
    for i, v in enumerate([same_party_strong, cross_party_strong]):
        axes[1].text(i, v + 10, str(v), ha="center", fontsize=11)

    plt.suptitle("Strong Triadic Closure Analysis (L6)", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "08_strong_triadic_closure.png"), dpi=200)
    plt.close()

    return {
        "median_weight_threshold": round(median_w, 6),
        "strong_ties": len(strong_edges),
        "weak_ties": len(weak_edges),
        "stc_tests": total_tests,
        "stc_violations": violations,
        "stc_satisfaction_pct": round((1 - violation_rate) * 100, 2),
        "strong_within_party": same_party_strong,
        "strong_cross_party": cross_party_strong,
    }


# ─────────────────────────────────────────────────────────────────────────────
# L6 — Bridges, Gatekeeper nodes
# ─────────────────────────────────────────────────────────────────────────────

def analyse_bridges_gatekeepers(G, users):
    print("\n[L6] Bridge and gatekeeper analysis...")
    G_ud = G.to_undirected()

    bridges = list(nx.bridges(G_ud))
    articulation_pts = list(nx.articulation_points(G_ud))
    print(f"  Bridges: {len(bridges)}")
    print(f"  Articulation points: {len(articulation_pts)}")

    betweenness = nx.betweenness_centrality(G, k=150, normalized=True)
    node_party = {n: users.get(n, {}).get("Party", None) for n in G.nodes()}

    gatekeepers = []
    for n in G.nodes():
        p = node_party.get(n)
        if p not in ("Democrat", "Republican"):
            continue
        cross = sum(1 for nb in list(G.successors(n)) + list(G.predecessors(n))
                    if node_party.get(nb) not in (p, None))
        if cross >= 3 and betweenness.get(n, 0) > np.quantile(list(betweenness.values()), 0.8):
            gatekeepers.append((n, cross, betweenness[n]))
    gatekeepers.sort(key=lambda x: x[1], reverse=True)

    print(f"  Top gatekeepers: {[users.get(n,{}).get('Users','?') for n,_,_ in gatekeepers[:10]]}")

    with open(os.path.join(RES_DIR, "bridges_articulation.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "username", "party", "betweenness", "is_articulation", "is_gatekeeper"])
        gk_ids = {n for n, _, _ in gatekeepers}
        for n in sorted(set(articulation_pts) | gk_ids, key=lambda x: betweenness.get(x, 0), reverse=True)[:30]:
            u = users.get(n, {})
            writer.writerow([n, u.get("Users", ""), u.get("Party", ""),
                              round(betweenness.get(n, 0), 6),
                              n in articulation_pts, n in gk_ids])

    top_art = sorted(articulation_pts + [n for n, _, _ in gatekeepers],
                     key=lambda n: betweenness.get(n, 0), reverse=True)[:20]
    top_art = list(dict.fromkeys(top_art))  # deduplicate preserving order
    names = [users.get(n, {}).get("Users", str(n)) for n in top_art]
    bw_vals = [betweenness[n] for n in top_art]
    art_colors = [PARTY_COLORS.get(node_party.get(n), "#aec7e8") for n in top_art]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(names[::-1], bw_vals[::-1], color=art_colors[::-1])
    ax.set_xlabel("Betweenness Centrality")
    ax.set_title("Top Gatekeeper Nodes by Betweenness Centrality\n(blue = Democrat, red = Republican)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "08_articulation_points.png"), dpi=200)
    plt.close()

    return bridges, articulation_pts, gatekeepers


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    G = load_graph()
    users = load_users()
    G_ud = G.to_undirected()

    print("Computing layout...")
    pos = nx.spring_layout(G_ud, seed=42, k=0.18, iterations=100)

    core_numbers, max_core = analyse_kcore(G, users, pos)
    community_strength = analyse_community_strength(G, users)
    f_measure = analyse_fmeasure(G)
    pct_within, pct_cross = analyse_homophily(G, users)
    trans, avg_clust, triangles, triples = analyse_transitivity(G)
    stc = analyse_strong_triadic_closure(G, users)
    bridges, articulation_pts, gatekeepers = analyse_bridges_gatekeepers(G, users)

    summary = {
        "L5_max_kcore": int(max_core),
        "L5_fmeasure": round(f_measure, 6),
        "L4_strong_communities": sum(1 for r in community_strength if r["strong_community"]),
        "L4_weak_communities": sum(1 for r in community_strength if not r["strong_community"]),
        "L6_within_party_pct": round(pct_within, 2),
        "L6_cross_party_pct": round(pct_cross, 2),
        "L6_global_transitivity": round(trans, 4),
        "L6_avg_local_clustering": round(avg_clust, 4),
        "L6_triangles": triangles,
        "L6_connected_triples": triples,
        "L6_bridges": len(bridges),
        "L6_articulation_points": len(articulation_pts),
        "L6_stc_satisfaction_pct": stc["stc_satisfaction_pct"],
        "L6_strong_ties": stc["strong_ties"],
        "L6_weak_ties": stc["weak_ties"],
        "L6_strong_within_party_pct": round(stc["strong_within_party"] / max(stc["strong_ties"], 1) * 100, 1),
    }

    with open(os.path.join(RES_DIR, "advanced_analysis_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=== ADVANCED ANALYSIS SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\nSaved: results/advanced_analysis_summary.json")
    print("Saved: figures/08_kcore_*.png, 08_community_strength.png, 08_homophily_bar.png, 08_strong_triadic_closure.png, 08_articulation_points.png")


if __name__ == "__main__":
    main()
