"""
Export congress.edgelist to a GEXF that preserves direction and weights.

Use this file in Gephi (not an undirected export) so visual exploration matches
the directed analyses in ../codes/ (utils.load_graph reads the same edgelist).

Run from anywhere:
  python3 convert_to_gexf_directed.py
"""
from pathlib import Path

import networkx as nx

HERE = Path(__file__).resolve().parent
EDGELIST = HERE / "congress.edgelist"
OUT_GEXF = HERE / "congress_directed.gexf"

G = nx.read_edgelist(
    EDGELIST,
    create_using=nx.DiGraph(),
    nodetype=int,
    data=True,
)

for _, _, data in G.edges(data=True):
    data["weight"] = float(data.get("weight", 1.0))

nx.write_gexf(G, OUT_GEXF)

print(f"Wrote {OUT_GEXF}")
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Directed:", G.is_directed())
