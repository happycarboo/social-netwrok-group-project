"""
Centrality measures — L3 (degree, closeness, betweenness, eigenvector)
plus Viral Centrality from the dataset paper (ICM-based, uses edge weights
as transmission probabilities).
"""

import ast
import csv
import os
import sys

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

# viral_centrality.py lives alongside this script
sys.path.insert(0, CODES_DIR)


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


def load_vc_scores():
    vc_path = os.path.join(RES_DIR, "viral_centrality_scores.csv")
    if not os.path.exists(vc_path):
        return {}
    scores = {}
    with open(vc_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores[int(row["node_id"])] = float(row["viral_centrality"])
    return scores


def bar_chart_top20(values_dict, label, filename, color="steelblue"):
    top20 = sorted(values_dict.items(), key=lambda x: x[1], reverse=True)[:20]
    nodes, vals = zip(*top20)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.barh([str(n) for n in nodes][::-1], list(vals)[::-1], color=color)
    ax.set_xlabel(label)
    ax.set_title(f"Top 20 Nodes — {label}")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), dpi=200)
    plt.close()


def compute_viral_centrality(users):
    """Run VC if scores CSV does not already exist."""
    vc_path = os.path.join(RES_DIR, "viral_centrality_scores.csv")
    if os.path.exists(vc_path):
        print("  VC scores already computed, loading from file.")
        return load_vc_scores()

    import json
    from viral_centrality import viral_centrality

    with open(os.path.join(DATA_DIR, "congress_network_data.json"), encoding="utf-8") as f:
        data = json.load(f)[0]

    tol = 0.001
    num_activated = viral_centrality(
        data["inList"], data["inWeight"], data["outList"], Niter=-1, tol=tol
    )
    scores = {i: float(v) for i, v in enumerate(num_activated)}

    node_ids = list(range(len(num_activated)))
    username_list = data["usernameList"]
    results = np.column_stack((node_ids, username_list, num_activated))
    np.savetxt(
        vc_path, results, delimiter=",", fmt="%s",
        header="node_id,username,viral_centrality", comments=""
    )
    print(f"  VC scores computed and saved to {vc_path}")
    return scores


def main():
    G = load_graph()
    users = load_users()
    nodes = list(G.nodes())

    # ── L3: Degree centrality (in/out degree and strength) ───────────────────
    print("Computing degree centrality (L3)...")
    out_deg = dict(G.out_degree())
    in_deg = dict(G.in_degree())
    out_str = {n: sum(d for _, _, d in G.out_edges(n, data="weight", default=0)) for n in nodes}
    in_str = {n: sum(d for _, _, d in G.in_edges(n, data="weight", default=0)) for n in nodes}

    # ── L3: Betweenness centrality ────────────────────────────────────────────
    print("Computing betweenness centrality (L3, approx k=100)...")
    betweenness = nx.betweenness_centrality(G, k=100, normalized=True)

    # ── L3: Closeness centrality ──────────────────────────────────────────────
    print("Computing closeness centrality (L3)...")
    closeness = nx.closeness_centrality(G)

    # ── L3: Eigenvector centrality ────────────────────────────────────────────
    print("Computing eigenvector centrality (L3)...")
    try:
        eigenvector = nx.eigenvector_centrality(G, weight="weight", max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        print("  Eigenvector did not converge, using unweighted.")
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000)

    # ── Viral Centrality (ICM-based, uses edge weights as P_ij) ──────────────
    print("Loading / computing Viral Centrality (ICM model)...")
    vc_scores = compute_viral_centrality(users)

    # ── Build results table ───────────────────────────────────────────────────
    rows = []
    for n in nodes:
        u = users.get(n, {})
        rows.append({
            "node_id": n,
            "username": u.get("Users", ""),
            "full_name": u.get("Full Name", ""),
            "party": u.get("Party", ""),
            "chamber": u.get("Chamber", ""),
            "out_degree": out_deg.get(n, 0),
            "in_degree": in_deg.get(n, 0),
            "out_strength": round(out_str.get(n, 0), 6),
            "in_strength": round(in_str.get(n, 0), 6),
            "betweenness": round(betweenness.get(n, 0), 6),
            "closeness": round(closeness.get(n, 0), 6),
            "eigenvector": round(eigenvector.get(n, 0), 6),
            "viral_centrality": round(vc_scores.get(n, 0), 6),
        })

    rows.sort(key=lambda x: x["viral_centrality"], reverse=True)

    out_csv = os.path.join(RES_DIR, "centrality_table.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: results/centrality_table.csv ({len(rows)} rows)")

    # ── Bar charts ────────────────────────────────────────────────────────────
    def named(d):
        return {users.get(n, {}).get("Users", str(n)): v for n, v in d.items()}

    bar_chart_top20(named(out_str),    "Out-Strength",          "02_top20_out_strength.png",    "tomato")
    bar_chart_top20(named(in_str),     "In-Strength",           "02_top20_in_strength.png",     "steelblue")
    bar_chart_top20(named(betweenness),"Betweenness Centrality","02_top20_betweenness.png",     "mediumpurple")
    bar_chart_top20(named(closeness),  "Closeness Centrality",  "02_top20_closeness.png",       "seagreen")
    bar_chart_top20(named(eigenvector),"Eigenvector Centrality","02_top20_eigenvector.png",     "darkorange")
    if vc_scores:
        bar_chart_top20(named(vc_scores), "Viral Centrality",   "02_top20_viral_centrality.png","goldenrod")

    print("Saved: figures/02_top20_*.png")


if __name__ == "__main__":
    main()
