import json
import random
import networkx as nx
import pandas as pd
import numpy as np

from viral_centrality import viral_centrality

# ==============================
# SETTINGS
# ==============================
EDGE_FILE = "congress.edgelist"
JSON_FILE = "congress_network_data.json"
USERS_FILE = "users.xlsx"
USERS_SHEET = "Sheet2"

RANDOM_RUNS = 50
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ==============================
# LOAD DATA
# ==============================
def load_graph(path):
    G = nx.read_edgelist(
        path,
        create_using=nx.DiGraph(),
        nodetype=int,
        data=True
    )
    for _, _, data in G.edges(data=True):
        data["weight"] = float(data.get("weight", 1.0))
    return G


def load_json_network(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return (
        data[0]["inList"],
        data[0]["inWeight"],
        data[0]["outList"],
        data[0]["outWeight"],
        data[0]["usernameList"]
    )


def load_users(path):
    df = pd.read_excel(path, sheet_name=USERS_SHEET)
    df.columns = [str(c).strip() for c in df.columns]
    df["id"] = df["id"].astype(int)
    return df


# ==============================
# HELPERS
# ==============================
def make_weak_projection(G):
    U = nx.Graph()
    U.add_nodes_from(G.nodes())

    for u, v, data in G.edges(data=True):
        w = float(data.get("weight", 1.0))
        if w <= 0:
            continue

        if U.has_edge(u, v):
            if w > U[u][v]["weight"]:
                U[u][v]["weight"] = w
                U[u][v]["distance"] = 1.0 / w
        else:
            U.add_edge(u, v, weight=w, distance=1.0 / w)

    return U


def get_basic_metrics(G):
    result = {}
    result["num_nodes"] = G.number_of_nodes()
    result["num_edges"] = G.number_of_edges()

    weak_components = list(nx.weakly_connected_components(G))
    result["num_weak_components"] = len(weak_components)

    largest_weak = max(len(c) for c in weak_components)
    result["largest_weak_component_size"] = largest_weak
    result["fragmentation_weak"] = 1 - (largest_weak / G.number_of_nodes())

    U = make_weak_projection(G)
    U_lcc = U.subgraph(max(nx.connected_components(U), key=len)).copy()

    try:
        result["diameter_lcc_unweighted"] = nx.diameter(U_lcc)
    except Exception:
        result["diameter_lcc_unweighted"] = np.nan

    return result


def print_metrics(title, m):
    print(f"\n--- {title} ---")
    print(f"Nodes: {m['num_nodes']}")
    print(f"Edges: {m['num_edges']}")
    print(f"Weak components: {m['num_weak_components']}")
    print(f"Largest weak component: {m['largest_weak_component_size']}")
    print(f"Fragmentation: {m['fragmentation_weak']:.4f}")
    print(f"Diameter (weak projection): {m['diameter_lcc_unweighted']}")


# ==============================
# MAIN
# ==============================
print("Loading graph...")
G = load_graph(EDGE_FILE)

print("Loading JSON network...")
inList, inWeight, outList, outWeight, usernameList = load_json_network(JSON_FILE)

print("Loading users metadata from Sheet2...")
df_users = load_users(USERS_FILE)

# ==============================
# BASELINE
# ==============================
baseline_metrics = get_basic_metrics(G)
print_metrics("BASELINE NETWORK", baseline_metrics)

# ==============================
# INFLUENTIAL NODES (Viral Centrality)
# ==============================
print("\nComputing Viral Centrality...")
vc_values = viral_centrality(inList, inWeight, outList, Niter=-1, tol=0.001)

vc_df = pd.DataFrame({
    "node_id": list(range(len(vc_values))),
    "viral_centrality": vc_values
}).sort_values("viral_centrality", ascending=False)

vc_df = vc_df.merge(df_users, how="left", left_on="node_id", right_on="id")

print("\nTop 10 influential nodes (Viral Centrality):")
print(vc_df[["node_id", "Users", "Full Name", "Party", "Chamber", "State/District", "viral_centrality"]].head(10).to_string(index=False))

# composition
print("\nParty composition among top 10 influential nodes:")
print(vc_df.head(10)["Party"].value_counts(dropna=False).to_string())

print("\nChamber composition among top 10 influential nodes:")
print(vc_df.head(10)["Chamber"].value_counts(dropna=False).to_string())

# what-if remove influential nodes
N = G.number_of_nodes()
removal_sizes = [1, 5, 10, max(1, round(0.05 * N))]

print("\n==============================")
print("WHAT-IF 1A: REMOVE INFLUENTIAL NODES")
print("==============================")

for k in removal_sizes:
    remove_nodes = vc_df.head(k)["node_id"].tolist()

    G_removed = G.copy()
    G_removed.remove_nodes_from(remove_nodes)

    m = get_basic_metrics(G_removed)
    print_metrics(f"After removing top {k} influential nodes", m)

# random benchmark
print("\nRandom removal benchmark (average over 50 runs):")
for k in removal_sizes:
    metric_list = []
    all_nodes = list(G.nodes())

    for _ in range(RANDOM_RUNS):
        sampled = random.sample(all_nodes, k)
        G_rand = G.copy()
        G_rand.remove_nodes_from(sampled)
        metric_list.append(get_basic_metrics(G_rand))

    avg_fragmentation = np.mean([x["fragmentation_weak"] for x in metric_list])
    avg_components = np.mean([x["num_weak_components"] for x in metric_list])
    avg_lcc = np.mean([x["largest_weak_component_size"] for x in metric_list])

    print(f"\nRandom remove {k} nodes:")
    print(f"Avg weak components: {avg_components:.2f}")
    print(f"Avg largest weak component: {avg_lcc:.2f}")
    print(f"Avg fragmentation: {avg_fragmentation:.4f}")

# ==============================
# BRIDGING NODES (Betweenness)
# ==============================
print("\nComputing bridging nodes (betweenness on weak projection)...")
U = make_weak_projection(G)
bet = nx.betweenness_centrality(U, weight="distance", normalized=True)

bet_df = pd.DataFrame({
    "node_id": list(bet.keys()),
    "betweenness": list(bet.values())
}).sort_values("betweenness", ascending=False)

bet_df = bet_df.merge(df_users, how="left", left_on="node_id", right_on="id")

print("\nTop 10 bridging nodes (Betweenness):")
print(bet_df[["node_id", "Users", "Full Name", "Party", "Chamber", "State/District", "betweenness"]].head(10).to_string(index=False))

print("\nParty composition among top 10 bridging nodes:")
print(bet_df.head(10)["Party"].value_counts(dropna=False).to_string())

print("\nChamber composition among top 10 bridging nodes:")
print(bet_df.head(10)["Chamber"].value_counts(dropna=False).to_string())

# articulation points
articulation_points = list(nx.articulation_points(U))
art_df = pd.DataFrame({"node_id": articulation_points}).merge(
    df_users, how="left", left_on="node_id", right_on="id"
)

print("\nArticulation points in weak projection:")
if len(art_df) == 0:
    print("None")
else:
    print(art_df[["node_id", "Users", "Full Name", "Party", "Chamber", "State/District"]].to_string(index=False))

print("\n==============================")
print("WHAT-IF 1B: REMOVE BRIDGING NODES")
print("==============================")

for k in removal_sizes:
    remove_nodes = bet_df.head(k)["node_id"].tolist()

    G_removed = G.copy()
    G_removed.remove_nodes_from(remove_nodes)

    m = get_basic_metrics(G_removed)
    print_metrics(f"After removing top {k} bridging nodes", m)

# ==============================
# CHANGE EDGE WEIGHT / BETA
# ==============================
print("\n==============================")
print("WHAT-IF 2: CHANGE TRANSMISSION PROBABILITIES")
print("==============================")

betas = [0.5, 0.8, 1.0, 1.2, 1.5]

for beta in betas:
    vc_beta = viral_centrality(inList, inWeight, outList, Niter=-1, beta=beta, tol=0.001)

    df_beta = pd.DataFrame({
        "node_id": list(range(len(vc_beta))),
        "viral_centrality": vc_beta
    }).sort_values("viral_centrality", ascending=False)

    df_beta = df_beta.merge(df_users, how="left", left_on="node_id", right_on="id")

    top1 = df_beta.iloc[0]

    print(f"\nBeta = {beta}")
    print(f"Mean Viral Centrality: {np.mean(vc_beta):.4f}")
    print(f"Max Viral Centrality: {np.max(vc_beta):.4f}")
    print(f"Top node: {top1['Users']} | {top1['Party']} | {top1['Chamber']} | VC={top1['viral_centrality']:.4f}")

    print("Top 5 nodes:")
    print(df_beta[["node_id", "Users", "Party", "Chamber", "viral_centrality"]].head(5).to_string(index=False))

print("\n==============================")
print("DONE")
print("==============================")