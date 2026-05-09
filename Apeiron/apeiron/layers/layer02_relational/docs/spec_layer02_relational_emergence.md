# Layer 2 – Relational Emergence (Formal Specification)

## 1. Introduction
Layer 2 takes the irreducible *UltimateObservables* produced by Layer 1 and organises them into a **weighted hypergraph** whose edges capture probabilistic co‑activation or mutual influence. This layer implements the transition from *substance* to *relation*: the identity of an observable is no longer intrinsic but constituted by its position in the relational network.

## 2. Formal Definitions

### 2.1 Weighted Hypergraph
Let $\mathcal{O} = \{o_1,\dots,o_N\}$ be the set of Layer‑1 observables active at a given time.  
A **relational hypergraph** is a triple $H = (\mathcal{O}, E, w)$, where  

* $E \subseteq \bigcup_{k=1}^{K_{\max}} \mathcal{O}^k$ is a set of hyperedges (irreducible $k$-ary relations),  
* $w: E \to [0,1]$ is a weight function, normalised so that $\sum_{e\in E} w(e) = 1$ (or simply $w(e)$ is the probability that $e$ is active).

### 2.2 Induced Pairwise Adjacency
For any two observables $o_i, o_j\in\mathcal{O}$, the effective pairwise adjacency is  

\[
A_{ij} = \sum_{\substack{e\in E \\ \{o_i,o_j\}\subseteq e}} \frac{w(e)}{\binom{|e|}{2}}\cdot \mathbf{1}[e\text{ active}].
\]

The matrix $A$ is symmetric, non‑negative, and hollow ($A_{ii}=0$).

### 2.3 Probabilistic Semantics
The weight $w(e)$ is not static but depends on the system’s state. Formally,

\[
w(e) = \frac{\exp(\psi_e(\mathbf{v}_{o_{i_1}},\dots,\mathbf{v}_{o_{i_k}}))}
{\sum_{e'\in E}\exp(\psi_{e'}(\dots))},
\]

where $\psi_e$ is a compatibility function defined on the values of the participating observables. This makes $H$ a *dynamic* hypergraph that responds to contextual cues.

## 3. Sublayers of Relational Structure

### 3.1 Dyadic Correlations
The simplest substructure: $k=2$. The adjacency matrix $A_{ij}$ captures pairwise correlations, standard network representation.

### 3.2 Functional Dependencies
Asymmetric, directed influences detected via Granger causality or transfer entropy:

\[
o_i \to o_j \quad\text{iff}\quad I(o_j(t+1); o_i(t) \mid \mathcal{O}\setminus\{o_i,o_j\}) > \epsilon.
\]

### 3.3 Higher‑Order Motifs
Recurrent $k$-ary sub‑hypergraphs identified through tensor decomposition (e.g., non‑negative Tucker decomposition) or frequent subgraph mining. Statistically over‑represented motifs are the seeds for functional clusters (Layer 3).

## 4. Emergence Criteria

### 4.1 Excess Entropy
Let $\mathbf{X}_t$ be the vector of observable states. The excess entropy

\[
E = I(\mathbf{X}_{\text{past}}; \mathbf{X}_{\text{future}}) - \sum_{i=1}^{|\mathcal{O}|} I(X_{i,\text{past}}; X_{i,\text{future}})
\]

quantifies how much better the whole predicts its future than the sum of its parts. $E > 0$ is a necessary condition for weak emergence.

### 4.2 Spectral Gap
The unnormalised Laplacian $L = D - A$ has eigenvalues $0 = \lambda_1 \le \lambda_2 \le \dots \le \lambda_N$.  
$\lambda_2 > 0$ indicates a connected graph; the magnitude of $\lambda_2$ (spectral gap) correlates with the stability of clusters.

### 4.3 Percolation Threshold
When the average relational density $\rho = \frac{1}{N(N-1)}\sum_{i\neq j}A_{ij}$ exceeds a critical value $\rho_c$, a giant connected component emerges, marking a macroscopic phase transition.

## 5. Implementation (Refactored Module Structure)

As of version 5.0, the formal components are realised by the following Python modules inside `apeiron.layers.layer02_relational`:

| Module | Purpose |
|--------|---------|
| `relations_core.py` | `UltimateRelation` – the rich edge object; `Layer2_Relational_Ultimate` – the manager that builds and indexes the relational network. |
| `category.py` | Categorical structures (categories, functors, natural transformations, adjunctions, …) that can be attached to relations. |
| `quiver.py` | Quivers (directed multigraphs) and their representations. |
| `spectral.py` | `SpectralGraphAnalysis`, `DynamicSpectralAnalysis`, and related spectral invariants that directly compute $\lambda_2$, excess entropy approximations, and spectral clustering. |
| `hypergraph.py` | `Hypergraph` – the direct incarnation of the formal $H = (\mathcal{O}, E, w)$, including Betti numbers and Hodge Laplacians for higher‑order structure. |
| `quantum_graph.py` | `QuantumGraph` – extends the hypergraph with quantum amplitudes, enabling quantum walks and entanglement measures. |
| `motif_detection.py` | `MotifCounter`, `PersistentHomology`, `TemporalMotifDetector`, `TopologicalNetworkAnalysis` – tools for detecting statistically over‑represented motifs (sublayer 3.3). |
| `causal_discovery.py` | `CausalDiscovery` – implements Granger causality and constraint‑based causal discovery (functional dependencies, sublayer 3.2). |
| `metric.py` | `RelationalMetricSpace` – supports Gromov‑Hausdorff and Wasserstein distances between relational structures. |
| `temporal_networks.py` | `TemporalNetwork`, `TemporalGraph` – dynamic community detection and forecasting over time. |
| `probabilistic_models.py` | Bayesian networks, Markov random fields, and HMMs that can be associated with relations. |
| `layer1_bridge.py` | Helper functions that convert Layer‑1 data into the formats required by Layer 2. |
| `graph_rl.py`, `multi_agent_rl.py`, `rl_on_graphs.py` | Reinforcement learning environments and agents operating on the relational substrate (optional). |
| `mapper.py` | Mapper algorithm for topological data analysis. |
| `dashboards.py` | Static Plotly figures for persistence diagrams, spectra, hypergraphs, etc. |
| `visualization_dash.py` | Interactive Dash applications built on top of `dashboards.py`. |

All heavy optional dependencies (Qiskit, PennyLane, PyTorch Geometric, …) reside in `apeiron/optional/` and are loaded lazily. This modular organisation keeps the core of Layer 2 lightweight while allowing domain‑specific extensions to be added without altering the fundamental architecture.

## 6. Public API

The **primary interface** for users is the class `Layer2_Relational_Ultimate` (in `relations_core.py`). A typical workflow is:

```python
from apeiron.layers.layer02_relational import Layer2_Relational_Ultimate, RelationType

layer2 = Layer2_Relational_Ultimate(layer1_registry=my_observables)
layer2.compute_relations(threshold=0.5)          # automatically build the hypergraph
stats = layer2.get_stats()                       # number of relations, by type, …

For spectral analysis of the emerging network:

python
from apeiron.layers.layer02_relational import SpectralGraphAnalysis
sa = SpectralGraphAnalysis(layer2.global_graph)
gap = sa.spectral_gap()                          # λ₂
The complete list of exported names is maintained in layer02_relational/__init__.py.