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

## 5. Public API Specification

```python
class RelationalHypergraph:
    """
    Holds the dynamic weighted hypergraph for a set of UltimateObservables.

    Parameters
    ----------
    observables : dict[str, UltimateObservable]
    k_max : int, default 5
    """

    def update(self, observable: UltimateObservable) -> None:
        """Add or update a single observable and recalculate affected edges."""

    def get_adjacency(self) -> np.ndarray:
        """Return the N×N effective adjacency matrix A."""

    def get_hyperedges(self, k: int) -> list[tuple]:
        """Return all hyperedges of arity k with their current weights."""

    def get_motifs(self, k: int, min_weight: float) -> list[tuple]:
        """Return statistically over‑represented k‑ary motifs."""

    def excess_entropy(self, history: list[np.ndarray]) -> float:
        """Compute excess entropy from a sequence of state vectors."""

    def spectral_gap(self) -> float:
        """Return the spectral gap λ₂ of the current adjacency matrix."""