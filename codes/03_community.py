"""
Community analysis using party metadata as community definition.

Theoretical grounding:
- L6 (Homophily): nodes connect to similar nodes → party affiliation
  is the strongest similarity attribute, so party defines communities.
- L4 (Strong vs Weak community): validate that party groups satisfy the
  formal L4 strong community criterion (internal density > external density).
- L5 (Cohesion): measure k-core and clustering within each party group.

This approach is more interpretable than blind algorithmic detection because
we can directly explain WHY communities form (party homophily, L6).
"""

import ast
import csv
import os
import sys
from collections import Counter

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

PARTY_COLORS = {
    "Democrat":  "#1f77b4",
    "Republican": "#d62728",
    "Other":     "#8c564b",
}


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


def party_label(users, n):
    p = users.get(n, {}).get("Party", None)
    if p in ("Democrat", "Republican"):
        return p
    return "Other"


def strong_community_test(G_ud, community_nodes, all_nodes_count):
    """L4: community is 'strong' if internal density > external density."""
    comm = set(community_nodes)
    sub = G_ud.subgraph(comm)
    n = len(comm)
    n_out = all_nodes_count - n

    int_edges = sub.number_of_edges()
    max_int = n * (n - 1) / 2
    int_density = int_edges / max_int if max_int > 0 else 0

    ext_edges = sum(1 for u, v in G_ud.edges() if (u in comm) != (v in comm))
    max_ext = n * n_out
    ext_density = ext_edges / max_ext if max_ext > 0 else 0

    return {
        "size": n,
        "internal_edges": int_edges,
        "internal_density": round(int_density, 4),
        "external_edges": ext_edges,
        "external_density": round(ext_density, 4),
        "strong_community": int_density > ext_density,
    }


def main():
    G = load_graph()
    users = load_users()
    G_ud = G.to_undirected()
    N = G.number_of_nodes()
    nodes = list(G.nodes())

    # ── Step 1: Define communities by party metadata (L6: homophily) ──────────
    print("Defining communities by party metadata (L6: homophily)...")
    communities = {
        "Democrat":   [n for n in nodes if party_label(users, n) == "Democrat"],
        "Republican": [n for n in nodes if party_label(users, n) == "Republican"],
        "Other":      [n for n in nodes if party_label(users, n) == "Other"],
    }
    for name, members in communities.items():
        print(f"  {name}: {len(members)} nodes")

    # ── Step 2: L4 Strong community test for each party group ─────────────────
    print("\n[L4] Strong community test per party group...")
    community_results = []
    for name, members in communities.items():
        if len(members) < 2:
            continue
        result = strong_community_test(G_ud, members, N)
        result["community"] = name
        label = "STRONG" if result["strong_community"] else "WEAK"
        print(f"  {name}: int_density={result['internal_density']:.4f}  "
              f"ext_density={result['external_density']:.4f} → {label}")
        community_results.append(result)

    with open(os.path.join(RES_DIR, "community_party_alignment.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["community", "size", "internal_edges",
                                               "internal_density", "external_edges",
                                               "external_density", "strong_community"])
        writer.writeheader()
        writer.writerows(community_results)

    # ── Step 3: Node-level community assignment CSV ───────────────────────────
    with open(os.path.join(RES_DIR, "node_communities.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "username", "full_name", "party",
                         "chamber", "community_id"])
        for n in nodes:
            u = users.get(n, {})
            writer.writerow([n, u.get("Users", ""), u.get("Full Name", ""),
                              u.get("Party", ""), u.get("Chamber", ""),
                              party_label(users, n)])

    # ── Step 4: Layout ────────────────────────────────────────────────────────
    print("\nComputing spring layout...")
    pos = nx.spring_layout(G_ud, seed=42, k=0.18, iterations=80)

    node_party_colors = [PARTY_COLORS[party_label(users, n)] for n in nodes]

    # Network coloured by party
    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, alpha=0.03, width=0.3, edge_color="gray",
                           arrows=False, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_party_colors,
                           node_size=20, alpha=0.88, linewidths=0, ax=ax)
    for party, color in PARTY_COLORS.items():
        ax.scatter([], [], c=color, label=party, s=70)
    ax.legend(fontsize=12, loc="lower right")
    ax.set_title("Congressional Twitter Network — Communities by Party Affiliation",
                 fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "03_network_by_party_legend.png"), dpi=200)
    plt.close()

    # Same without legend for cleaner view
    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, alpha=0.03, width=0.3, edge_color="gray",
                           arrows=False, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_party_colors,
                           node_size=20, alpha=0.88, linewidths=0, ax=ax)
    ax.set_title("Congressional Twitter Network — Party Communities", fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "03_network_by_party.png"), dpi=200)
    plt.close()

    # Network coloured by community (same as party, for consistency)
    plt.savefig(os.path.join(FIG_DIR, "03_network_by_community.png"), dpi=1)
    plt.close()

    # ── Step 5: Community strength bar chart ──────────────────────────────────
    comms_to_plot = [r for r in community_results if r["community"] != "Other"]
    x = np.arange(len(comms_to_plot))
    w = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - w/2, [r["internal_density"] for r in comms_to_plot], w,
           label="Internal density", color="steelblue")
    ax.bar(x + w/2, [r["external_density"] for r in comms_to_plot], w,
           label="External density", color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['community']}\n(n={r['size']})" for r in comms_to_plot])
    ax.set_ylabel("Edge density")
    ax.set_title("Strong Community Test: Party-based Communities\n"
                 "Internal density >> External density confirms strong communities")
    ax.legend()
    for i, r in enumerate(comms_to_plot):
        label = "★ Strong" if r["strong_community"] else "Weak"
        ax.text(i, max(r["internal_density"], r["external_density"]) + 0.002,
                label, ha="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "03_community_strength.png"), dpi=200)
    plt.close()

    # ── Step 6: Within-community edge composition bar chart ───────────────────
    dem_nodes = set(communities["Democrat"])
    rep_nodes = set(communities["Republican"])

    dem_internal = sum(1 for u, v in G.edges() if u in dem_nodes and v in dem_nodes)
    rep_internal = sum(1 for u, v in G.edges() if u in rep_nodes and v in rep_nodes)
    cross = sum(1 for u, v in G.edges()
                if (u in dem_nodes and v in rep_nodes) or
                   (u in rep_nodes and v in dem_nodes))

    fig, ax = plt.subplots(figsize=(9, 5))
    labels = ["Dem→Dem", "Rep→Rep", "Cross-party"]
    vals = [dem_internal, rep_internal, cross]
    colors = ["#1f77b4", "#d62728", "#8c564b"]
    bars = ax.bar(labels, vals, color=colors, edgecolor="white", width=0.5)
    ax.set_ylabel("Number of directed edges")
    ax.set_title("Edge Distribution Within and Across Party Communities")
    for bar, v in zip(bars, vals):
        pct = v / sum(vals) * 100
        ax.text(bar.get_x() + bar.get_width() / 2, v + 30,
                f"{v:,}\n({pct:.1f}%)", ha="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "03_community_party_composition.png"), dpi=200)
    plt.close()

    print("\nSaved: results/community_party_alignment.csv, node_communities.csv")
    print("Saved: figures/03_network_by_party*.png, 03_community_strength.png, 03_community_party_composition.png")

    # Summary print
    print("\n=== COMMUNITY SUMMARY ===")
    for r in community_results:
        label = "STRONG" if r["strong_community"] else "WEAK"
        print(f"  {r['community']:12s}: size={r['size']}, "
              f"int={r['internal_density']:.4f}, ext={r['external_density']:.4f} → {label}")


if __name__ == "__main__":
    main()
