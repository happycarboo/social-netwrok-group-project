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