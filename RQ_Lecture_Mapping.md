# Research Questions → Lecture Knowledge Mapping

This document maps each research question (as originally written) to the lecture concepts that can be used to answer it. Questions sharing the same core knowledge are grouped where natural.

---

## RQ 1 — Community Differences

### Q1.1: How can the users be categorised?

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L4 — Subnetworks** | Clique, n-clique, n-clan, n-club | Identify tightly-connected subgroups algorithmically (e.g. clique percolation, modularity-based detection) |
| **L5 — Cohesion** | k-core, k-plex, components, fragmentation | k-core peels the network to reveal cohesive shells; connected components show natural partitions |
| **L6 — Ties** | Homophily | Use node attributes (party, chamber, state) as the basis for categorisation — homophily predicts that ties cluster along shared attributes |

**Approach options:**
- *Attribute-based partition* (party from metadata) — grounded in L6 homophily.
- *Structural detection* (Girvan–Newman, Louvain, greedy modularity) — grounded in L4 subnetworks.
- *Cohesion shells* (k-core decomposition) — grounded in L5.

---

### Q1.2: How do the categories differ from one another?

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L1 — Network Basics** | Density = edges / possible edges | Compare within-group density vs cross-group density for each community |
| **L2 — Network Metrics** | Average path length, small-world property | Compare average path length within each community and between communities |
| **L3 — Centrality** | Degree, closeness, betweenness, eigenvector | Compare centrality distributions across groups (e.g. do Republicans have higher mean out-degree than Democrats?) |
| **L5 — Cohesion** | k-core membership, clustering coefficient | Which community dominates the inner core? Does clustering coefficient differ by group? |
| **L6 — Ties** | Reciprocity, strong vs weak ties | Compare reciprocity rate and strong-tie fraction within each community |

---

### Q1.3 + Q1.4: Is the network structurally centralised around a few dominant members? Does it exhibit high degree centralisation or betweenness centralisation?

*These two questions target the same concept (Freeman centralisation) — one asks "is it centralised?", the other asks "which type?"*

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L3 — Centrality** | Freeman's degree centralisation, betweenness centralisation | Compute a single whole-network centralisation index for degree and for betweenness. A high value (close to 1) means the network resembles a star — a few nodes dominate. A low value means influence is distributed. Comparing the two reveals whether dominance is via *popularity* (degree) or *brokerage* (betweenness). |
| **L2 — Network Metrics** | Density, connectivity | Low density + high centralisation = hub-and-spoke; low density + low centralisation = distributed sparse network |

**How to answer:**
- Freeman's degree centralisation = \(\frac{\sum_{i}[C_D^* - C_D(i)]}{(n-1)(n-2)}\) for directed graphs.
- Freeman's betweenness centralisation = \(\frac{\sum_{i}[C_B^* - C_B(i)]}{\max \text{ possible}}\).
- Report both numbers and compare: e.g. "betweenness centralisation is higher than degree centralisation, indicating the network is organised around a few *brokers* rather than a few *hubs*."

---

### Supplementary: Compare Democratic vs Republican, Senate vs House

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L6 — Ties** | Homophily | Measure within-group vs cross-group tie ratio for party *and* chamber |
| **L1 / L2** | Density, path length | Report descriptive stats broken down by chamber (House vs Senate) and party |
| **L5 — Cohesion** | k-core | Which chamber/party is over-represented in the densest core? |

---

## RQ 2 — Focus on Influence

### Q2.1: Who are the most influential users, and why?

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L3 — Centrality** | Degree (popularity), closeness (speed of reach), betweenness (brokerage/control), eigenvector (influence via important neighbours) | Rank nodes by each measure. "Why" = which *type* of centrality they score highest on explains the nature of their influence. |
| **L9 — Network Dynamics** | Cascade model, threshold \(p \geq b/(a+b)\) | Viral Centrality (from the dataset paper) is an ICM cascade simulation — directly applies the cascade/threshold idea from L9 |
| **L10 — Network Effects** | SIR/SIS, \(R_0 = p \times k\) | VC is conceptually the expected "outbreak size" seeded at a node — connects to \(R_0\) thinking |

---

### Q2.2: Is there an imbalance of influence where influence is not reciprocated?

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L6 — Ties** | Reciprocity | Network-level reciprocity (fraction of mutual edges). Low reciprocity = asymmetric influence. Compare reciprocity within vs across parties. |
| **L3 — Centrality** | In-degree vs out-degree, in-strength vs out-strength | Nodes with high out-strength but low in-strength are "broadcasters" (influence not returned). Nodes with high in-strength but low out-strength are "receivers". The gap between the two reveals the imbalance. |

---

### Q2.3: Are the influential users balanced across parties?

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L3 — Centrality** | All centrality measures | Count how many of the top-N by each centrality belong to each party. |
| **L6 — Ties** | Homophily | If influence is party-homophilous, the top influencers within each community may differ from the top influencers network-wide. |
| **L5 — Cohesion** | k-core | Party composition of the innermost core reveals which party has broader structural coordination (a different form of "influence balance"). |

---

## RQ 3 — Cross-Party Influence

### Q3.1 + Q3.3: To what extent is there cross-party influence? Is there stronger influence within the same party?

*These two questions are two sides of the same coin — within-party vs cross-party tie strength.*

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L6 — Ties** | Homophily, strong vs weak ties | Compute within-party vs cross-party edge share (count and weight). Classify ties as strong/weak by weight threshold; check if cross-party ties are predominantly weak. |
| **L6 — Ties** | Triadic closure | If triadic closure is high within-party and low cross-party, information stays trapped inside partisan clusters. |
| **L8 — Information Flow** | Flow network, max-flow min-cut, bottleneck | Model the party boundary as a "cut" — the max-flow across that cut quantifies how much information *can* cross party lines. Low max-flow = strong echo chamber. |

**Metrics to report:**
- % of edges within-party vs cross-party (count and weight)
- Strong ties: what fraction are cross-party?
- Party-to-party flow matrix (D→D, D→R, R→D, R→R)

---

### Q3.2: Are there critical bridging nodes that act as articulation points?

| Lecture | Key concepts | How it applies |
|---|---|---|
| **L3 — Centrality** | Betweenness centrality | High-betweenness nodes sitting on cross-party shortest paths are structural brokers. |
| **L5 — Cohesion** | Components, fragmentation | An articulation point is a node whose removal disconnects the graph (increases component count). Check if any exist. If none, the network is *bi-connected* — resilient but may still have *near*-articulation points (high betweenness). |
| **L8 — Information Flow** | Bottleneck, max-flow min-cut | Nodes appearing in many minimum cuts between party blocks are information bottlenecks — "gatekeepers." |
| **L6 — Ties** | Strong vs weak ties | Granovetter: weak ties are the ones that *bridge* communities. Check whether cross-party edges are predominantly weak ties. |

---

## Summary: Lecture Coverage per RQ

| Lecture | RQ1 Community | RQ2 Influence | RQ3 Cross-party |
|---|---|---|---|
| L1 — Network Basics | Density comparisons | | |
| L2 — Network Metrics | Path length, small-world | | |
| **L3 — Centrality** | **Centralisation indices** | **Individual rankings, in/out imbalance** | **Betweenness for bridging** |
| L4 — Subnetworks | Community detection | | |
| **L5 — Cohesion** | **k-core, clustering** | **k-core party balance** | **Articulation points, fragmentation** |
| **L6 — Ties** | **Homophily, reciprocity** | **Reciprocity imbalance** | **Homophily, strong/weak ties, triadic closure** |
| L7 — Structural Balance | (optional: +/- ties) | | |
| **L8 — Information Flow** | | | **Max-flow, bottleneck, gatekeeper** |
| **L9 — Network Dynamics** | | **Cascade / VC** | |
| **L10 — Network Effects** | | **SIR/SIS, R₀** | |
| L11 — Platform Governance | | | (implications section) |
| L12 — Course Integration | Ties all together | Ties all together | Ties all together |

**Bold** = primary relevance. Every lecture from L1–L10 has a natural home in at least one RQ.
