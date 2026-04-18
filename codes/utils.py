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
    """Load directed weighted graph from edgelist.

    Canonical source: congress_network/congress.edgelist (same as
    congress_directed.gexf from convert_to_gexf_directed.py for Gephi).
    """
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
    users_path = os.path.join(DATA_DIR, "users 2.xlsx")
    if not os.path.exists(users_path):
        raise FileNotFoundError(
            f"User metadata not found: {users_path}. "
            "Add congress_network/users 2.xlsx (canonical, up-to-date metadata)."
        )
    wb = openpyxl.load_workbook(users_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    users = {}
    for r in rows[1:]:
        if r[0] is None:
            continue
        record = dict(zip(header, r))
        state_district = record.get("State/District")
        if state_district:
            # Keep state as a dedicated field for easier grouping.
            record["State"] = str(state_district).split("-", 1)[0].strip()
        else:
            record["State"] = None
        users[int(r[0])] = record
    return users


def party_of(users, n):
    """Return 'Democrat', 'Republican', or 'Other' for a node."""
    p = users.get(n, {}).get("Party", None)
    if p in ("Democrat", "Republican"):
        return p
    return "Other"


def username_of(users, n):
    return users.get(n, {}).get("Users", str(n))


def state_of(users, n):
    """Return normalised state name/abbr for a node."""
    s = users.get(n, {}).get("State", None)
    if s:
        return s
    sd = users.get(n, {}).get("State/District", None)
    if not sd:
        return "Unknown"
    return str(sd).split("-", 1)[0].strip() or "Unknown"


def save_fig(fig, name):
    fig.savefig(os.path.join(FIG_DIR, name), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: figures/{name}")
