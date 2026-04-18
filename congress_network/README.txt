This directory contains data for the Congressional Twitter network used in 
"A centrality measure for quantifying spread on weighted, directed networks" (Fink et. al., Physica A, 2023)
and
"A Congressional Twitter network dataset quantifying pairwise probability of influence" (Fink et. al., Data in Brief, 2023)

The dataset was collected using the Twitter API (please see the Methods sections of the above papers
for further details on how the network was constructed).

This dataset was posted by Christian G. Fink, Gonzaga University (finkt@gonzaga.edu)

congress_network_data.json contains the following data:

inList: list of lists such that inList[i] is a list of all the nodes sending connections TO node i
inWeight: list of lists containing the connection weights (transmission probabilities) corresponding to the connections in inList
outList: list of lists such that outList[i] is a list of all the nodes receiving connections FROM node i
outWeight: list of lists containing the connection weights (transmission probabilities) corresponding to the connections in outList
usernameList[i] gives the Twitter username corresponding to node i

congress.edgelist contains the weighted, directed edgelist for the Congressional network, in NetworkX format

User metadata for analysis scripts is loaded from users 2.xlsx only (updated fields
such as State/District / chamber). The stock users.xlsx from some downloads is
not used.

Gephi / GEXF (directed)
-----------------------
All Python scripts under ../codes/ load congress.edgelist as a directed graph
(NetworkX DiGraph). If you open an undirected GEXF in Gephi, or merge A->B with
B->A, degree/betweenness/SCC metrics will NOT match the report.

For Gephi, generate a directed GEXF from the same edgelist:

  python3 convert_to_gexf_directed.py

This writes congress_directed.gexf (graph defaultedgetype="directed"). Import
that file and keep the graph type directed in Gephi so group visual checks align
with the full analysis.

This folder is kept as a data-only source directory for the group project.
All analysis scripts have been moved to ../codes/.

See also https://github.com/gsprint23/CongressionalTwitterNetwork for code for re-hydrating the original Twitter data.

Current workflow
----------------
Run analyses from the sibling ../codes/ directory. Example:

python3 ../codes/01_network_structure.py
python3 ../codes/02_centrality.py
python3 ../codes/03_community.py
python3 ../codes/04_cross_party.py
python3 ../codes/05_egocentric.py
python3 ../codes/06_whatif.py
python3 ../codes/07_network_viz.py
python3 ../codes/08_community_advanced.py

Outputs are written under ../codes/results/ and ../codes/figures/.