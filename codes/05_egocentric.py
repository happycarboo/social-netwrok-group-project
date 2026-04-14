"""Egocentric network analysis for top influential node."""

import ast
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

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


def draw_ego(G_ego, ego_id, users, title, filename):
    party_colors = {n: PARTY_COLORS.get(users.get(n, {}).get("Party", ""), "#aec7e8") for n in G_ego.nodes()}

    pos = nx.spring_layout(G_ego, seed=42, k=0.35)
    node_sizes = [300 if n == ego_id else 60 for n in G_ego.nodes()]
    node_colors = [party_colors[n] for n in G_ego.nodes()]

    # Edge thickness by weight
    weights = [G_ego[u][v].get("weight", 0.001) * 15 for u, v in G_ego.edges()]

    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G_ego, pos, width=weights, alpha=0.4, edge_color="gray", arrows=True,
                           arrowsize=8, ax=ax)
    nx.draw_networkx_nodes(G_ego, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9,
                           linewidths=0.5, edgecolors="white", ax=ax)

    # Label only the ego node
    ego_label = {ego_id: users.get(ego_id, {}).get("Users", str(ego_id))}
    nx.draw_networkx_labels(G_ego, pos, labels=ego_label, font_size=10, font_weight="bold", ax=ax)

    for party, color in PARTY_COLORS.items():
        ax.scatter([], [], c=color, label=party, s=60)
    ax.legend(fontsize=10, loc="lower right")
    ax.set_title(title, fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), dpi=200)
    plt.close()


def main():
    G = load_graph()
    users = load_users()

    # Find top node by out-strength (SteveScalise)
    username_to_id = {v.get("Users", ""): k for k, v in users.items()}

    # Primary ego: SteveScalise (top VC), Secondary: SpeakerPelosi
    egos = [
        (username_to_id.get("SteveScalise"), "SteveScalise"),
        (username_to_id.get("SpeakerPelosi"), "SpeakerPelosi"),
    ]

    for ego_id, ego_name in egos:
        if ego_id is None:
            print(f"Could not find {ego_name} in users.xlsx, skipping.")
            continue

        neighbors = set(G.successors(ego_id)) | set(G.predecessors(ego_id))
        ego_nodes = {ego_id} | neighbors
        G_ego = G.subgraph(ego_nodes).copy()

        n_nodes = G_ego.number_of_nodes()
        n_edges = G_ego.number_of_edges()
        print(f"Ego network for {ego_name}: {n_nodes} nodes, {n_edges} edges")

        # Party breakdown
        from collections import Counter
        party_counts = Counter(users.get(n, {}).get("Party", "Unknown") for n in G_ego.nodes())
        print(f"  Party breakdown: {dict(party_counts)}")

        # Reciprocated edges
        reciprocated = sum(1 for u, v in G_ego.edges() if G_ego.has_edge(v, u)) // 2
        print(f"  Reciprocated edges: {reciprocated}")

        draw_ego(
            G_ego, ego_id, users,
            f"1-hop Ego Network of {ego_name} ({n_nodes} nodes, {n_edges} edges)",
            f"05_ego_{ego_name}.png",
        )
        print(f"Saved: figures/05_ego_{ego_name}.png")


if __name__ == "__main__":
    main()
