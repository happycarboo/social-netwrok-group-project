import networkx as nx

G = nx.read_edgelist(
    'congress.edgelist',
    create_using=nx.DiGraph(),
    nodetype=int,
    data=True
)

for u, v, data in G.edges(data=True):
    data['weight'] = float(data.get('weight', 1.0))

nx.write_gexf(G, 'congress.gexf')

print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
