"""Shared data-loading and helper functions for all analysis scripts."""

import ast
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "congress_network")
FIG_DIR = os.path.join(BASE_DIR, "figures")
RES_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

CLR_DEM = "#1f77b4"
CLR_REP = "#d62728"
CLR_OTH = "#8c564b"

PARTY_COLORS = {"Democrat": CLR_DEM, "Republican": CLR_REP, "Other": CLR_OTH}
PARTIES = ["Democrat", "Republican", "Other"]

CLR_DEM_LIGHT = "#aec7e8"
CLR_REP_LIGHT = "#ff9896"
CLR_INTERNAL = CLR_DEM        # for within-group bars
CLR_EXTERNAL = CLR_REP        # for cross-group bars
CLR_NEUTRAL = "#7f7f7f"       # gray for non-party items


def load_graph():
    """Load directed weighted graph from edgelist."""
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
    """Load user metadata from Excel file."""
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


def party_of(users, n):
    """Return 'Democrat', 'Republican', or 'Other' for a node."""
    p = users.get(n, {}).get("Party", None)
    if p in ("Democrat", "Republican"):
        return p
    return "Other"


def username_of(users, n):
    return users.get(n, {}).get("Users", str(n))


def save_fig(fig, name):
    fig.savefig(os.path.join(FIG_DIR, name), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: figures/{name}")
