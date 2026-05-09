"""
BENCHMARKS – Prestatiemeting voor Layer 2 (Relational Dynamics)
================================================================
Dit bestand bevat een uitgebreide benchmark-suite voor het meten van
prestaties van de algoritmen in Layer 2. Het ondersteunt:

- Timing van individuele functies
- Geheugenprofiling (met memory_profiler)
- Schaalbaarheidstests (variërende grafengrootte, dichtheid, etc.)
- Opslag van resultaten in CSV/JSON
- Visualisatie met matplotlib/plotly
- Integratie met pytest-benchmark (optioneel)

Gebruik:
    from from apeiron.benchmark.layer02_benchmarks import BenchmarkSuite
    suite = BenchmarkSuite()
    suite.run_all()
    suite.save_results('benchmark_results.json')
    suite.plot_results()

Of via command line:
    python -m from apeiron.benchmark.layer02_benchmarks [--plot] [--save]

Integratie met pytest-benchmark:
    In een pytest-testbestand kun je de suite als volgt gebruiken:
        def test_benchmark(benchmark):
            suite = BenchmarkSuite()
            register_benchmarks(suite)
            result = benchmark(suite.run_benchmark, "spectral_eigensystem",
                               {"n_nodes": 100, "p": 0.1})
            assert result.time_ms > 0
"""

import time
import json
import csv
import os
import sys
import logging
import inspect
from typing import Dict, List, Any, Callable, Optional, Tuple, Union
from functools import wraps
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import argparse

import numpy as np

# ============================================================================
# OPTIONAL DEPENDENCY CHECKS – GRACEFUL DEGRADATION
# ============================================================================

# Memory profiling
try:
    from memory_profiler import memory_usage
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

# Plotting
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Data handling
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Graph libraries
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# Scientific libraries
try:
    import scipy
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn import __version__ as sklearn_version
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Causal discovery
try:
    import causallearn
    HAS_CAUSALLEARN = True
except ImportError:
    HAS_CAUSALLEARN = False

try:
    import lingam
    HAS_LINGAM = True
except ImportError:
    HAS_LINGAM = False

# Topological data analysis
try:
    import gudhi
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

try:
    import kmapper
    HAS_KMAPPER = True
except ImportError:
    HAS_KMAPPER = False

# Quantum ML
try:
    import pennylane
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False

# Time series
try:
    import statsmodels
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    import ruptures
    HAS_RUPTURES = True
except ImportError:
    HAS_RUPTURES = False

# Deep learning
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import torch_geometric
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

# Reinforcement learning
try:
    import gym
    HAS_GYM = True
except ImportError:
    try:
        import gymnasium
        HAS_GYM = True
    except ImportError:
        HAS_GYM = False

# Database
try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

# ============================================================================
# Imports van de te benchmarken modules
# ============================================================================
from . import adjacency_matrix
from . import hypergraph_relations
from . import motif_detection
from . import relations
from . import causal_discovery
from . import rl_on_graphs
from . import multi_agent_rl
from . import probabilistic_models
from . import quantum_ml
from . import temporal_networks
from . import graph_self_supervised
from . import derived_categories
from . import layer1_bridge
from . import density_field
from . import discovery
from . import qualitative_dimensions
from . import decomposition
from . import meta_spec
from . import atomicity_visuals

# ============================================================================
# Dataclass voor resultaten
# ============================================================================

@dataclass
class BenchmarkResult:
    """Resultaat van één benchmark-run."""
    name: str
    parameters: Dict[str, Any]
    time_ms: float
    memory_mb: Optional[float] = None
    output: Any = None  # eventuele returnwaarde voor verificatie
    error: Optional[str] = None


# ============================================================================
# Kernklasse BenchmarkSuite
# ============================================================================

class BenchmarkSuite:
    """
    Bevat een verzameling benchmarks en voert ze uit met verschillende parameters.
    """

    def __init__(self, name: str = "Layer2 Benchmark Suite"):
        self.name = name
        self.benchmarks: Dict[str, Callable] = {}  # naam -> functie
        self.results: List[BenchmarkResult] = []
        self.logger = logging.getLogger(__name__)

    def register(self, func: Optional[Callable] = None, *, name: Optional[str] = None):
        """
        Decorator om een functie als benchmark te registreren.
        Gebruik:
            @suite.register
            def my_benchmark(param1, param2):
                ...

            @suite.register(name="custom_name")
            def my_benchmark(...): ...
        """
        def decorator(f):
            bench_name = name or f.__name__
            self.benchmarks[bench_name] = f
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper
        if func is not None:
            return decorator(func)
        return decorator

    def run_benchmark(self, name: str, params: Dict[str, Any], profile_memory: bool = False) -> BenchmarkResult:
        """
        Voer een specifieke benchmark uit met gegeven parameters.
        Optioneel met geheugenprofiling.
        """
        if name not in self.benchmarks:
            raise ValueError(f"Benchmark '{name}' niet gevonden")
        func = self.benchmarks[name]

        # Bereid de argumenten voor: match parameters met functiehandtekening
        sig = inspect.signature(func)
        kwargs = {k: v for k, v in params.items() if k in sig.parameters}

        start = time.perf_counter()
        mem_usage = None
        error = None
        output = None

        if profile_memory and HAS_MEMORY_PROFILER:
            # memory_usage geeft lijst van geheugengebruik tijdens uitvoering (in MiB)
            try:
                mem_usage, output = memory_usage((func, (), kwargs), retval=True, interval=0.1, include_children=True)
                max_mem = max(m[1] for m in mem_usage) if mem_usage else None
                elapsed_ms = (mem_usage[-1][0] - mem_usage[0][0]) * 1000  # laatste timestamp - eerste timestamp
            except Exception as e:
                error = str(e)
                elapsed_ms = 0
                max_mem = None
        else:
            try:
                output = func(**kwargs)
            except Exception as e:
                error = str(e)
                self.logger.error(f"Benchmark {name} mislukt: {e}")
            end = time.perf_counter()
            elapsed_ms = (end - start) * 1000
            max_mem = None

        result = BenchmarkResult(
            name=name,
            parameters=params,
            time_ms=elapsed_ms,
            memory_mb=max_mem,
            output=output,
            error=error
        )
        self.results.append(result)
        return result

    def run_all(self, param_grid: Dict[str, List[Any]], profile_memory: bool = False,
                filter_names: Optional[List[str]] = None):
        """
        Voer alle geregistreerde benchmarks uit (of een subset) met een grid van parameters.
        param_grid: mapping van parameternaam naar lijst van waarden (cartesisch product).
        """
        from itertools import product
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        for combo in product(*values):
            params = dict(zip(keys, combo))
            for bench_name in self.benchmarks:
                if filter_names and bench_name not in filter_names:
                    continue
                self.run_benchmark(bench_name, params, profile_memory)

    def save_results(self, filename: str, format: str = 'json'):
        """Sla resultaten op in JSON of CSV."""
        if format == 'json':
            data = [asdict(r) for r in self.results]
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            if not HAS_PANDAS:
                raise ImportError("Pandas vereist voor CSV-export")
            df = pd.DataFrame([asdict(r) for r in self.results])
            df.to_csv(filename, index=False)
        else:
            raise ValueError(f"Onbekend formaat: {format}")

    def load_results(self, filename: str):
        """Laad resultaten uit een JSON-bestand."""
        with open(filename, 'r') as f:
            data = json.load(f)
        self.results = [BenchmarkResult(**item) for item in data]

    def plot_results(self, x_param: str, y_metric: str = 'time_ms', group_by: Optional[str] = None,
                     use_plotly: bool = False, filename: Optional[str] = None):
        """
        Visualiseer resultaten.
        x_param: parameternaam op x-as
        y_metric: 'time_ms' of 'memory_mb'
        group_by: parameternaam om kleur/groep te bepalen
        """
        if not self.results:
            self.logger.warning("Geen resultaten om te plotten")
            return

        # Converteer naar DataFrame voor gemakkelijke verwerking
        if HAS_PANDAS:
            df = pd.DataFrame([asdict(r) for r in self.results])
        else:
            df = None

        if use_plotly and HAS_PLOTLY:
            self._plot_plotly(df, x_param, y_metric, group_by, filename)
        elif HAS_MATPLOTLIB:
            self._plot_matplotlib(df, x_param, y_metric, group_by, filename)
        else:
            self.logger.warning("Geen visualisatiebibliotheek beschikbaar")

    def _plot_matplotlib(self, df, x_param, y_metric, group_by, filename):
        plt.figure(figsize=(10, 6))
        if df is not None:
            if group_by:
                for group, group_df in df.groupby(group_by):
                    plt.plot(group_df[x_param], group_df[y_metric], 'o-', label=str(group))
                plt.legend()
            else:
                plt.plot(df[x_param], df[y_metric], 'o-')
        else:
            # Handmatig groeperen (als geen pandas)
            groups = defaultdict(list)
            for r in self.results:
                if group_by:
                    key = r.parameters.get(group_by, 'none')
                    groups[key].append(r)
                else:
                    groups['all'].append(r)
            for label, reslist in groups.items():
                x = [r.parameters[x_param] for r in reslist]
                y = [getattr(r, y_metric) for r in reslist]
                # Sorteer op x
                xy = sorted(zip(x, y))
                x, y = zip(*xy)
                plt.plot(x, y, 'o-', label=label if group_by else None)
            if group_by:
                plt.legend()
        plt.xlabel(x_param)
        plt.ylabel(y_metric)
        plt.title(f"Benchmark: {y_metric} vs {x_param}")
        plt.grid(True)
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        plt.close()

    def _plot_plotly(self, df, x_param, y_metric, group_by, filename):
        if df is not None:
            if group_by:
                fig = px.line(df, x=x_param, y=y_metric, color=group_by, markers=True)
            else:
                fig = px.line(df, x=x_param, y=y_metric, markers=True)
        else:
            # Handmatig
            data = []
            groups = defaultdict(list)
            for r in self.results:
                if group_by:
                    key = r.parameters.get(group_by, 'none')
                    groups[key].append(r)
                else:
                    groups['all'].append(r)
            for label, reslist in groups.items():
                x = [r.parameters[x_param] for r in reslist]
                y = [getattr(r, y_metric) for r in reslist]
                xy = sorted(zip(x, y))
                x, y = zip(*xy)
                data.append(go.Scatter(x=x, y=y, mode='lines+markers', name=str(label)))
            fig = go.Figure(data=data)
        fig.update_layout(title=f"Benchmark: {y_metric} vs {x_param}",
                          xaxis_title=x_param,
                          yaxis_title=y_metric)
        if filename:
            fig.write_html(filename)
        else:
            fig.show()


# ============================================================================
# Hulpfuncties voor het genereren van testdata
# ============================================================================

class BenchmarkDataGenerator:
    """Genereer testdata voor benchmarks."""

    @staticmethod
    def random_graph(n_nodes: int, p: float = 0.1, directed: bool = False, seed: int = 42):
        if not HAS_NETWORKX:
            raise ImportError("NetworkX vereist voor graafgeneratie")
        if directed:
            return nx.erdos_renyi_graph(n_nodes, p, seed=seed, directed=True)
        else:
            return nx.erdos_renyi_graph(n_nodes, p, seed=seed)

    @staticmethod
    def random_hypergraph(n_vertices: int, n_hyperedges: int, max_size: int = 5, seed: int = 42):
        if not HAS_NETWORKX:
            raise ImportError("NetworkX vereist voor hypergraafgeneratie (voor graafbasis)")
        import random
        random.seed(seed)
        hg = hypergraph_relations.Hypergraph()
        vertices = list(range(n_vertices))
        hg.vertices = set(vertices)
        for i in range(n_hyperedges):
            size = random.randint(2, min(max_size, n_vertices))
            edge = set(random.sample(vertices, size))
            hg.add_hyperedge(f"e{i}", edge, weight=1.0)
        return hg

    @staticmethod
    def random_data_matrix(n_samples: int, n_vars: int, seed: int = 42):
        np.random.seed(seed)
        return np.random.randn(n_samples, n_vars)

    @staticmethod
    def random_time_series(n_steps: int, seed: int = 42):
        np.random.seed(seed)
        return np.cumsum(np.random.randn(n_steps))

    @staticmethod
    def random_quantum_state(n_qubits: int):
        dim = 2 ** n_qubits
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        return np.outer(psi, psi.conj())

    @staticmethod
    def generate_layer1_registry(
        num_observables: int,
        num_nodes: int,
        data_type: str = 'continuous',
        min_val: float = 0.0,
        max_val: float = 1.0,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genereer een realistische Layer 1‑registry met willekeurige observables.

        De registry heeft de vorm:
            {
                'observables': {
                    'obs_0': [val0, val1, ...],
                    'obs_1': [val0, val1, ...],
                    ...
                }
            }

        Args:
            num_observables: Aantal te genereren observable‑namen.
            num_nodes: Aantal nodes (lengte van elke observable‑lijst).
            data_type: 'continuous' voor floats, 'discrete' voor integers.
            min_val, max_val: Bereik van de gegenereerde waarden.
            seed: Seed voor reproduceerbaarheid.

        Returns:
            Dictionary met een 'observables'‑sleutel die een dict van naam‑>lijst bevat.
        """
        if seed is not None:
            np.random.seed(seed)

        observables = {}
        for i in range(num_observables):
            name = f"obs_{i}"
            if data_type == 'continuous':
                values = np.random.uniform(min_val, max_val, num_nodes).tolist()
            elif data_type == 'discrete':
                values = np.random.randint(int(min_val), int(max_val) + 1, num_nodes).tolist()
            else:
                raise ValueError(f"Onbekend data_type: {data_type}")
            observables[name] = values

        return {'observables': observables}


# ============================================================================
# Concrete benchmarkfuncties (uitgebreid)
# ============================================================================

def register_benchmarks(suite: BenchmarkSuite):
    """Registreer alle standaard benchmarks in de suite."""

    # ------------------------------------------------------------------------
    # adjacency_matrix
    # ------------------------------------------------------------------------
    @suite.register(name="spectral_eigensystem")
    def bench_spectral_eigensystem(n_nodes: int, p: float = 0.1, directed: bool = False,
                                    matrix_type: str = 'laplacian', k: int = 10):
        """Benchmark voor compute_eigensystem."""
        if not HAS_NETWORKX:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p, directed)
        from .adjacency_matrix import SpectralGraphAnalysis, SpectralType
        sa = SpectralGraphAnalysis(graph)
        mt = SpectralType.LAPLACIAN if matrix_type == 'laplacian' else SpectralType.ADJACENCY
        sa.compute_eigensystem(matrix_type=mt, k=k)
        return True

    @suite.register(name="spectral_clustering")
    def bench_spectral_clustering(n_nodes: int, p: float = 0.1, directed: bool = False,
                                   n_clusters: int = 3):
        if not HAS_NETWORKX:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p, directed)
        from .adjacency_matrix import SpectralGraphAnalysis
        sa = SpectralGraphAnalysis(graph)
        labels = sa.spectral_clustering(n_clusters=n_clusters)
        return labels

    @suite.register(name="spectral_invariants")
    def bench_spectral_invariants(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .adjacency_matrix import SpectralGraphAnalysis
        sa = SpectralGraphAnalysis(graph)
        inv = sa.get_invariants()
        return inv

    @suite.register(name="dynamic_spectral_analysis")
    def bench_dynamic_spectral(n_graphs: int = 5, n_nodes: int = 50, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        from .adjacency_matrix import DynamicSpectralAnalysis
        dsa = DynamicSpectralAnalysis()
        for i in range(n_graphs):
            G = BenchmarkDataGenerator.random_graph(n_nodes, p, seed=i)
            dsa.add_graph(G, timestamp=i)
        evo = dsa.compute_eigenvalue_evolution(k=5)
        return evo

    @suite.register(name="spectral_database")
    def bench_spectral_database(n_nodes: int, p: float = 0.1):
        if not HAS_SQLITE:
            return None
        from .adjacency_matrix import SpectralDatabase, SpectralGraphAnalysis
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        sa = SpectralGraphAnalysis(G)
        evals, evecs = sa.compute_eigensystem(k=5)
        db = SpectralDatabase(db_type='sqlite', connection_string=':memory:')
        db._create_sqlite_tables()
        db.store_spectrum("test", 0.0, "laplacian", evals, evecs)
        loaded = db.load_spectra("test", "laplacian")
        db.close()
        return len(loaded)

    # ------------------------------------------------------------------------
    # hypergraph_relations
    # ------------------------------------------------------------------------
    @suite.register(name="hypergraph_betti")
    def bench_hypergraph_betti(n_vertices: int, n_hyperedges: int, max_size: int = 5):
        hg = BenchmarkDataGenerator.random_hypergraph(n_vertices, n_hyperedges, max_size)
        betti = hg.betti_numbers()
        return betti

    @suite.register(name="hypergraph_hodge")
    def bench_hypergraph_hodge(n_vertices: int, n_hyperedges: int, max_size: int = 5):
        hg = BenchmarkDataGenerator.random_hypergraph(n_vertices, n_hyperedges, max_size)
        hodge_eig = hg.hodge_eigenvalues(dim=1, k=3)
        return hodge_eig

    @suite.register(name="quantum_walk_continuous")
    def bench_quantum_walk_continuous(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .hypergraph_relations import QuantumGraph
        qg = QuantumGraph(graph=G)
        init = np.zeros(n_nodes, dtype=complex)
        init[0] = 1.0
        final = qg.quantum_walk(time=1.0, initial_state=init, method='continuous')
        return final

    @suite.register(name="quantum_walk_discrete_coin")
    def bench_quantum_walk_discrete_coin(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .hypergraph_relations import QuantumGraph
        qg = QuantumGraph(graph=G)
        max_deg = max(dict(G.degree()).values())
        init = np.zeros(n_nodes * max_deg, dtype=complex)
        init[0] = 1.0
        final = qg.quantum_walk(time=5, initial_state=init, method='discrete_coin', coin_type='grover')
        return final

    @suite.register(name="quantum_pagerank")
    def bench_quantum_pagerank(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX or not HAS_SCIPY:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .hypergraph_relations import QuantumGraph
        qg = QuantumGraph(graph=G)
        pr = qg.quantum_pagerank()
        return pr

    @suite.register(name="entanglement_entropy")
    def bench_entanglement_entropy(n_qubits: int = 4):
        from .hypergraph_relations import QuantumGraph
        qg = QuantumGraph()
        rho = BenchmarkDataGenerator.random_quantum_state(n_qubits)
        qg.entanglement_matrix = rho
        entropy = qg.entanglement_entropy(partition=[0, 1])
        return entropy

    @suite.register(name="hypergraph_rl")
    def bench_hypergraph_rl(n_vertices: int, n_hyperedges: int, max_size: int = 5):
        if not HAS_GYM:
            return None
        hg = BenchmarkDataGenerator.random_hypergraph(n_vertices, n_hyperedges, max_size)
        from .hypergraph_relations import HypergraphEnv, RLAgent
        env = HypergraphEnv(hg, target=list(hg.vertices)[-1], max_steps=10)
        agent = RLAgent(env)
        agent.train(episodes=5)
        return True

    # ------------------------------------------------------------------------
    # motif_detection
    # ------------------------------------------------------------------------
    @suite.register(name="motif_triangles")
    def bench_motif_triangles(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import MotifCounter
        counter = MotifCounter(graph)
        return counter.count_triangles()

    @suite.register(name="motif_significance")
    def bench_motif_significance(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX or not HAS_SCIPY:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import MotifCounter, MotifType
        counter = MotifCounter(graph)
        sig = counter.motif_significance(MotifType.TRIANGLE, n_random=5)
        return sig

    @suite.register(name="persistent_homology_clique")
    def bench_persistent_homology_clique(n_nodes: int, p: float = 0.1, max_dim: int = 2):
        if not HAS_NETWORKX or not HAS_GUDHI:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import PersistentHomology
        ph = PersistentHomology(graph)
        ph.build_clique_complex(max_dim)
        ph.compute_persistence()
        return ph.diagrams

    @suite.register(name="persistent_homology_rips")
    def bench_persistent_homology_rips(n_nodes: int, p: float = 0.1, max_dim: int = 2):
        if not HAS_NETWORKX or not HAS_GUDHI:
            return None
        graph = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import PersistentHomology
        ph = PersistentHomology(graph)
        ph.build_vietoris_rips(max_edge_length=1.0, max_dim=max_dim, metric='shortest_path')
        ph.compute_persistence()
        return ph.diagrams

    @suite.register(name="temporal_motifs")
    def bench_temporal_motifs(n_nodes: int, p: float = 0.1, n_timestamps: int = 10):
        if not HAS_NETWORKX:
            return None
        # Maak een willekeurige temporele graaf
        edge_timestamps = {}
        for i in range(n_nodes):
            for j in range(i+1, n_nodes):
                if np.random.random() < p:
                    times = np.random.uniform(0, n_timestamps, size=5)
                    edge_timestamps[(i, j)] = times.tolist()
        from .motif_detection import TemporalMotifDetector
        detector = TemporalMotifDetector(edge_timestamps)
        count = detector.count_temporal_triangles(window=(0, n_timestamps))
        return count

    @suite.register(name="graph_kernel_wl")
    def bench_graph_kernel_wl(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        G1 = BenchmarkDataGenerator.random_graph(n_nodes, p)
        G2 = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import GraphKernel, GraphKernelType
        kernel = GraphKernel(GraphKernelType.WEISFEILER_LEHMAN)
        val = kernel.compute(G1, G2, h=2)
        return val

    @suite.register(name="graph_kernel_shortest_path")
    def bench_graph_kernel_shortest_path(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        G1 = BenchmarkDataGenerator.random_graph(n_nodes, p)
        G2 = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import GraphKernel, GraphKernelType
        kernel = GraphKernel(GraphKernelType.SHORTEST_PATH)
        val = kernel.compute(G1, G2)
        return val

    @suite.register(name="community_detection_louvain")
    def bench_community_detection_louvain(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import detect_communities_enhanced
        comm = detect_communities_enhanced(G, method='louvain')
        return comm

    @suite.register(name="community_detection_spectral")
    def bench_community_detection_spectral(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX or not HAS_SCIPY:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import detect_communities_enhanced
        comm = detect_communities_enhanced(G, method='spectral', n_clusters=2)
        return comm

    @suite.register(name="centralities")
    def bench_centralities(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        from .motif_detection import compute_centralities_extended
        cent = compute_centralities_extended(G)
        return cent

    @suite.register(name="mapper")
    def bench_mapper(n_nodes: int, p: float = 0.1):
        if not HAS_NETWORKX or not HAS_KMAPPER:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p)
        data = np.array([G.degree(v) for v in G.nodes()]).reshape(-1, 1)
        from .motif_detection import Mapper
        mapper = Mapper(data, lens=[data[:,0]])
        mapper.run()
        return mapper.graph is not None

    # ------------------------------------------------------------------------
    # relations (UltimateRelation, categorische operaties)
    # ------------------------------------------------------------------------
    @suite.register(name="create_relation")
    def bench_create_relation():
        from .relations import UltimateRelation, RelationType
        rel = UltimateRelation(
            id="test",
            source_id="src",
            target_id="tgt",
            relation_type=RelationType.SYMMETRIC,
            weight=0.5
        )
        return rel.id

    @suite.register(name="category_compose")
    def bench_category_compose(n_objects: int = 10, n_morphisms: int = 20):
        from .relations import RelationalCategory
        cat = RelationalCategory()
        for i in range(n_objects):
            cat.add_object(i)
        # Voeg willekeurige morfismen toe
        for _ in range(n_morphisms):
            s = np.random.randint(0, n_objects)
            t = np.random.randint(0, n_objects)
            cat.add_morphism(s, t, f"f_{s}_{t}")
        # Probeer enkele composities
        count = 0
        for (s, t), hom in cat.hom_sets.items():
            for f in hom:
                for (t2, u), hom2 in cat.hom_sets.items():
                    if t2 == t:
                        for g in hom2:
                            comp = cat.compose(f, g, s, t, u)
                            if comp is not None:
                                count += 1
        return count

    @suite.register(name="metric_space_distance")
    def bench_metric_space_distance(n_relations: int = 10):
        from .relations import RelationalMetricSpace, UltimateRelation, RelationType
        rels = []
        for i in range(n_relations):
            rel = UltimateRelation(
                id=f"rel{i}",
                source_id=f"src{i}",
                target_id=f"tgt{i}",
                relation_type=RelationType.SYMMETRIC,
                weight=np.random.random()
            )
            rels.append(rel)
        ms = RelationalMetricSpace(relations=rels)
        dist_matrix = ms.compute_all_distances(method='edit')
        return np.sum(dist_matrix)

    @suite.register(name="quantum_state_reduced_density")
    def bench_quantum_state_reduced_density(n_qubits: int = 5):
        from .relations import QuantumState
        rho = BenchmarkDataGenerator.random_quantum_state(n_qubits)
        qs = QuantumState(n_qubits, rho)
        rhoA = qs.reduced_density([0, 1])
        return np.trace(rhoA)

    @suite.register(name="compute_relations")
    def bench_compute_relations(
        n_observables: int = 5,
        n_nodes: int = 10,
        data_type: str = 'continuous'
    ):
        """
        Benchmark voor de functie compute_relations (uit relations.py)
        met verschillende aantallen observables.
        """
        # Genereer een Layer 1‑registry
        registry = BenchmarkDataGenerator.generate_layer1_registry(
            num_observables=n_observables,
            num_nodes=n_nodes,
            data_type=data_type,
            seed=42
        )

        # Probeer compute_relations aan te roepen; als het niet bestaat, sla over
        try:
            from .relations import compute_relations
        except (ImportError, AttributeError):
            return None

        # Voer de berekening uit
        result = compute_relations(registry)
        # Retourneer bijvoorbeeld het aantal gevonden relaties
        if result is None:
            return 0
        if hasattr(result, '__len__'):
            return len(result)
        return 1  # fallback

    # ------------------------------------------------------------------------
    # causal_discovery
    # ------------------------------------------------------------------------
    @suite.register(name="causal_pc")
    def bench_causal_pc(n_samples: int, n_vars: int, alpha: float = 0.05):
        if not HAS_CAUSALLEARN:
            return None
        data = BenchmarkDataGenerator.random_data_matrix(n_samples, n_vars)
        from .causal_discovery import CausalDiscovery
        cd = CausalDiscovery(data, [f"X{i}" for i in range(n_vars)])
        graph = cd.pc(alpha=alpha)
        return graph is not None

    @suite.register(name="causal_fci")
    def bench_causal_fci(n_samples: int, n_vars: int, alpha: float = 0.05):
        if not HAS_CAUSALLEARN:
            return None
        data = BenchmarkDataGenerator.random_data_matrix(n_samples, n_vars)
        from .causal_discovery import CausalDiscovery
        cd = CausalDiscovery(data, [f"X{i}" for i in range(n_vars)])
        graph = cd.fci(alpha=alpha)
        return graph is not None

    @suite.register(name="causal_lingam")
    def bench_causal_lingam(n_samples: int, n_vars: int):
        if not HAS_LINGAM:
            return None
        data = BenchmarkDataGenerator.random_data_matrix(n_samples, n_vars)
        from .causal_discovery import CausalDiscovery
        cd = CausalDiscovery(data, [f"X{i}" for i in range(n_vars)])
        graph = cd.lingam(method='ICALiNGAM')
        return graph is not None

    @suite.register(name="causal_ges")
    def bench_causal_ges(n_samples: int, n_vars: int):
        if not HAS_CAUSALLEARN:
            return None
        data = BenchmarkDataGenerator.random_data_matrix(n_samples, n_vars)
        from .causal_discovery import CausalDiscovery
        cd = CausalDiscovery(data, [f"X{i}" for i in range(n_vars)])
        graph = cd.ges()
        return graph is not None

    @suite.register(name="causal_notears")
    def bench_causal_notears(n_samples: int, n_vars: int):
        data = BenchmarkDataGenerator.random_data_matrix(n_samples, n_vars)
        from .causal_discovery import CausalDiscovery
        cd = CausalDiscovery(data, [f"X{i}" for i in range(n_vars)])
        graph = cd.notears(w_threshold=0.3)
        return graph is not None

    @suite.register(name="granger_causality")
    def bench_granger_causality(n_steps: int = 200):
        if not HAS_STATSMODELS:
            return None
        ts1 = BenchmarkDataGenerator.random_time_series(n_steps)
        ts2 = BenchmarkDataGenerator.random_time_series(n_steps)
        from .causal_discovery import CausalDiscovery
        data = np.column_stack([ts1, ts2])
        cd = CausalDiscovery(data, ["X0", "X1"])
        result = cd.granger_causality(0, 1, max_lag=3)
        return result['f_stat']

    # ------------------------------------------------------------------------
    # rl_on_graphs
    # ------------------------------------------------------------------------
    @suite.register(name="rl_qlearning")
    def bench_rl_qlearning(n_nodes: int, episodes: int = 10):
        if not HAS_NETWORKX or not HAS_GYM:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p=0.2)
        from .rl_on_graphs import GraphEnv, QLearningAgent, train_agent
        env = GraphEnv(G, target_node=n_nodes-1, max_steps=20, observation_mode='node')
        agent = QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n)
        results = train_agent(env, agent, episodes=episodes, verbose=False)
        return results['episode_rewards'][-1]

    @suite.register(name="rl_dqn")
    def bench_rl_dqn(n_nodes: int, episodes: int = 5):
        if not HAS_TORCH or not HAS_NETWORKX or not HAS_GYM:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p=0.2)
        from .rl_on_graphs import GraphEnv, DQNAgent, train_agent
        env = GraphEnv(G, target_node=n_nodes-1, max_steps=20, observation_mode='full')
        agent = DQNAgent(input_dim=env.n_nodes + env.n_nodes, output_dim=env.action_space.n)
        results = train_agent(env, agent, episodes=episodes, verbose=False)
        return results['episode_rewards'][-1]

    # ------------------------------------------------------------------------
    # multi_agent_rl
    # ------------------------------------------------------------------------
    @suite.register(name="multi_agent_qlearning")
    def bench_multi_agent_qlearning(n_nodes: int, n_agents: int = 2, episodes: int = 5):
        if not HAS_NETWORKX or not HAS_GYM:
            return None
        G = BenchmarkDataGenerator.random_graph(n_nodes, p=0.2)
        from .multi_agent_rl import MultiAgentGraphEnv, IndependentQLearningAgent, train_multi_agent
        env = MultiAgentGraphEnv(graph=G, n_agents=n_agents, max_steps=10, cooperative=True)
        agents = [IndependentQLearningAgent(agent_id=i,
                                            action_space=env.action_space_per_agent,
                                            observation_space=env.observation_space_per_agent)
                  for i in range(n_agents)]
        results = train_multi_agent(env, agents, episodes=episodes, verbose=False)
        return results['episode_rewards'][-1]

    # ------------------------------------------------------------------------
    # probabilistic_models
    # ------------------------------------------------------------------------
    @suite.register(name="bayesian_network_sample")
    def bench_bayesian_network_sample(n_samples: int = 100):
        from .probabilistic_models import BayesianNetwork
        bn = BayesianNetwork(edges=[('A','C'), ('B','C')],
                             variable_names=['A','B','C'],
                             cardinalities={'A':2, 'B':2, 'C':2})
        bn.set_cpd('A', np.array([0.5,0.5]), [])
        bn.set_cpd('B', np.array([0.5,0.5]), [])
        bn.set_cpd('C', np.array([[0.9,0.1],[0.2,0.8]]), ['A','B'])
        bn.is_fitted = True
        samples = bn.sample(n_samples)
        return samples.shape

    @suite.register(name="hmm_viterbi")
    def bench_hmm_viterbi(n_states: int = 3, n_obs: int = 5, seq_len: int = 50):
        from .probabilistic_models import HiddenMarkovModel
        hmm = HiddenMarkovModel(n_states, n_obs)
        obs_seq = np.random.randint(0, n_obs, size=seq_len)
        states = hmm.predict(obs_seq)
        return len(states)

    # ------------------------------------------------------------------------
    # quantum_ml
    # ------------------------------------------------------------------------
    @suite.register(name="quantum_kernel_matrix")
    def bench_quantum_kernel_matrix(n_points: int = 10, n_qubits: int = 2):
        if not HAS_PENNYLANE:
            return None
        from .quantum_ml import QuantumKernel
        kernel = QuantumKernel(n_qubits=n_qubits, encoding='angle')
        X = np.random.randn(n_points, n_qubits)
        K = kernel.kernel_matrix(X)
        return np.linalg.norm(K)

    @suite.register(name="qsvm_pennylane")
    def bench_qsvm_pennylane(n_train: int = 20, n_test: int = 10, n_qubits: int = 2):
        if not HAS_PENNYLANE or not HAS_SKLEARN:
            return None
        from .quantum_ml import QSVM
        X_train = np.random.randn(n_train, n_qubits)
        y_train = np.random.randint(0, 2, n_train)
        X_test = np.random.randn(n_test, n_qubits)
        y_test = np.random.randint(0, 2, n_test)
        qsvm = QSVM(backend='pennylane', n_qubits=n_qubits, encoding='angle')
        qsvm.fit(X_train, y_train)
        acc = qsvm.score(X_test, y_test)
        return acc

    # ------------------------------------------------------------------------
    # temporal_networks
    # ------------------------------------------------------------------------
    @suite.register(name="temporal_network_communities")
    def bench_temporal_network_communities(n_snapshots: int = 5, n_nodes: int = 50, p: float = 0.1):
        if not HAS_NETWORKX:
            return None
        from .temporal_networks import TemporalNetwork, dynamic_communities
        snapshots = []
        for i in range(n_snapshots):
            G = BenchmarkDataGenerator.random_graph(n_nodes, p, seed=i)
            snapshots.append(G)
        tn = TemporalNetwork(snapshots=snapshots, timestamps=list(range(n_snapshots)))
        comms = dynamic_communities(tn, method='louvain')
        return len(comms)

    @suite.register(name="change_point_detection")
    def bench_change_point_detection(n_steps: int = 200):
        if not HAS_RUPTURES:
            return None
        from .temporal_networks import detect_change_points
        series = np.concatenate([np.random.randn(50), np.random.randn(50)+2, np.random.randn(50)-1])
        changes = detect_change_points(series, method='ruptures')
        return len(changes)

    @suite.register(name="forecast_arima")
    def bench_forecast_arima(n_steps: int = 100):
        if not HAS_STATSMODELS:
            return None
        from .temporal_networks import forecast_next_snapshot
        series = np.cumsum(np.random.randn(n_steps))
        forecast = forecast_next_snapshot(series, steps=5, method='arima')
        return forecast[0]

    # ------------------------------------------------------------------------
    # graph_self_supervised
    # ------------------------------------------------------------------------
    @suite.register(name="graphcl_train_step")
    def bench_graphcl_train_step(n_nodes: int = 20, n_features: int = 10):
        if not HAS_TORCH or not HAS_PYG:
            return None
        import torch
        from torch_geometric.data import Data
        from .graph_self_supervised import GCNEncoder, GraphCL, node_dropping
        edge_index = torch.randint(0, n_nodes, (2, 2*n_nodes))
        x = torch.randn(n_nodes, n_features)
        data = Data(x=x, edge_index=edge_index)
        encoder = GCNEncoder(in_channels=n_features, hidden_channels=16, out_channels=8)
        proj = torch.nn.Linear(8, 8)
        model = GraphCL(encoder, proj, augment_fn=node_dropping)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        loss_dict = model.train_step(data, optimizer)
        return loss_dict['loss']

    # ------------------------------------------------------------------------
    # derived_categories
    # ------------------------------------------------------------------------
    @suite.register(name="chain_complex_homology")
    def bench_chain_complex_homology(dim: int = 10):
        from .derived_categories import ChainComplex
        # Maak een willekeurig ketencomplex met differentiaalmatrices
        d1 = np.random.randn(dim, dim)
        d2 = np.random.randn(dim, dim)
        C = ChainComplex([d1, d2])
        h1 = C.homology(1)[0]
        return h1

    # ------------------------------------------------------------------------
    # layer1_bridge
    # ------------------------------------------------------------------------
    @suite.register(name="bridge_extract_feature_matrix")
    def bench_bridge_extract_feature_matrix(n_obs: int = 10, n_nodes: int = 100):
        registry = BenchmarkDataGenerator.generate_layer1_registry(n_obs, n_nodes)
        obs_names = list(registry['observables'].keys())
        from .layer1_bridge import extract_feature_matrix
        X = extract_feature_matrix(registry, obs_names)
        return X.shape

    @suite.register(name="bridge_similarity_matrix")
    def bench_bridge_similarity_matrix(n_obs: int = 10, n_nodes: int = 100):
        registry = BenchmarkDataGenerator.generate_layer1_registry(n_obs, n_nodes)
        from .layer1_bridge import similarity_matrix
        sim = similarity_matrix(registry, method='cosine')
        return sim.shape

    @suite.register(name="bridge_registry_to_graph")
    def bench_bridge_registry_to_graph(n_obs: int = 10, n_nodes: int = 100):
        if not HAS_NETWORKX:
            return None
        registry = BenchmarkDataGenerator.generate_layer1_registry(n_obs, n_nodes)
        from .layer1_bridge import registry_to_graph
        G = registry_to_graph(registry, edge_definition='threshold', threshold=0.5)
        return G.number_of_nodes()

    @suite.register(name="bridge_discretize_observable")
    def bench_bridge_discretize_observable(n_values: int = 10000):
        values = np.random.randn(n_values)
        from .layer1_bridge import discretize_observable
        codes = discretize_observable(values, n_bins=10, strategy='quantile')
        return len(codes)

    # ------------------------------------------------------------------------
    # density_field
    # ------------------------------------------------------------------------
    @suite.register(name="density_field_compute_influence")
    def bench_density_field_compute_influence(n_obs: int = 50):
        # Create dummy observables with resonance maps
        class DummyObs:
            def __init__(self, idx):
                self.id = f"obs_{idx}"
                self.resonance_map = {"layerA": {"weight": np.random.rand()}}
                self.observer_perspective = "default"
        registry = {i: DummyObs(i) for i in range(n_obs)}
        from .density_field import DensityField
        field = DensityField()
        for obs in registry.values():
            field.add_observable(obs)
        # Compute influence for first observable
        infl = field.compute_influence(list(registry.keys())[0])
        return len(infl)

    # ------------------------------------------------------------------------
    # discovery
    # ------------------------------------------------------------------------
    @suite.register(name="discovery_heuristic_discover")
    def bench_discovery_heuristic_discover(n_samples: int = 100):
        data = [np.random.randn(10) for _ in range(n_samples)]
        from .discovery import HeuristicDiscovery
        discoverer = HeuristicDiscovery(data)
        proposals = discoverer.discover()
        return len(proposals)

    @suite.register(name="discovery_evolutionary_update")
    def bench_discovery_evolutionary_update(n_principles: int = 10):
        from .meta_spec import MetaSpecification
        from .discovery import EvolutionaryFeedbackLoop
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec)
        for i in range(n_principles):
            loop.record_usage(f"principle_{i}", success=(i%2==0))
        loop.update_weights()
        return len(loop.usage_counter)

    # ------------------------------------------------------------------------
    # qualitative_dimensions
    # ------------------------------------------------------------------------
    @suite.register(name="qualitative_colour_convert")
    def bench_qualitative_colour_convert(n_colours: int = 100):
        from .qualitative_dimensions import ColourDimension, ColourSpace
        colours = [ColourDimension([np.random.rand(), np.random.rand(), np.random.rand()],
                                   colour_space=ColourSpace.RGB) for _ in range(n_colours)]
        for c in colours:
            c.convert_to(ColourSpace.HSL)
        return len(colours)

    @suite.register(name="qualitative_vector_magnitude")
    def bench_qualitative_vector_magnitude(n_vectors: int = 100, dim: int = 10):
        from .qualitative_dimensions import VectorDimension
        vectors = [VectorDimension(f"v{i}", np.random.randn(dim)) for i in range(n_vectors)]
        mags = [v.magnitude() for v in vectors]
        return len(mags)

    # ------------------------------------------------------------------------
    # decomposition
    # ------------------------------------------------------------------------
    @suite.register(name="decomposition_is_atomic")
    def bench_decomposition_is_atomic(n_ops: int = 1000):
        from .decomposition import is_atomic_by_operator
        data = np.random.rand(10, 10)
        results = []
        for _ in range(n_ops):
            results.append(is_atomic_by_operator(data, "geometric_point"))
        return len(results)

    # ------------------------------------------------------------------------
    # meta_spec
    # ------------------------------------------------------------------------
    @suite.register(name="meta_spec_weight_update")
    def bench_meta_spec_weight_update(n_updates: int = 1000):
        from .meta_spec import MetaSpecification
        spec = MetaSpecification()
        for i in range(n_updates):
            spec.update_weight("boolean", np.random.rand())
        return spec.default_atomicity_weights["boolean"]

    # ------------------------------------------------------------------------
    # atomicity_visuals (skip if no matplotlib, but we can still run generation)
    # ------------------------------------------------------------------------
    @suite.register(name="atomicity_visuals_heatmap")
    def bench_atomicity_visuals_heatmap(n_rows: int = 50, n_cols: int = 50):
        if not HAS_MATPLOTLIB:
            return None
        from .atomicity_visuals import plot_atomicity_heatmap
        matrix = np.random.rand(n_rows, n_cols)
        # Save to temporary file to avoid showing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            plot_atomicity_heatmap(matrix, filename=f.name, show=False)
        return True


# ============================================================================
# Command-line interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Benchmark suite voor Layer 2")
    parser.add_argument('--save', type=str, default=None, help="Bestand om resultaten op te slaan (JSON)")
    parser.add_argument('--load', type=str, default=None, help="Laad resultaten uit JSON-bestand (geen nieuwe runs)")
    parser.add_argument('--plot', action='store_true', help="Plot resultaten na uitvoering")
    parser.add_argument('--x-param', type=str, default='n_nodes', help="Parameter voor x-as bij plot")
    parser.add_argument('--y-metric', type=str, default='time_ms', help="Metric voor y-as (time_ms of memory_mb)")
    parser.add_argument('--group-by', type=str, default=None, help="Parameter om op te groeperen")
    parser.add_argument('--use-plotly', action='store_true', help="Gebruik Plotly voor plots")
    parser.add_argument('--profile-memory', action='store_true', help="Profiel geheugengebruik (traag)")
    parser.add_argument('--filter', type=str, nargs='+', help="Alleen deze benchmarks uitvoeren")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    suite = BenchmarkSuite()

    if args.load:
        suite.load_results(args.load)
        logging.info(f"Resultaten geladen uit {args.load}")
    else:
        register_benchmarks(suite)

        # Definieer een parameter grid voor de benchmarks
        # Dit is een voorbeeld; kan worden aangepast
        param_grid = {
            'n_nodes': [10, 50, 100],
            'p': [0.1],
            'directed': [False],
            'n_clusters': [3],
            'max_dim': [2],
            'n_vertices': [10, 50],
            'n_hyperedges': [20, 50],
            'max_size': [4],
            'n_samples': [100],
            'n_vars': [5],
            'alpha': [0.05],
            'matrix_type': ['laplacian'],
            'k': [10],
            'n_graphs': [3],
            'n_qubits': [3],
            'n_objects': [5],
            'n_morphisms': [10],
            'n_relations': [5],
            'n_steps': [100],
            'n_agents': [2],
            'episodes': [5],
            'n_train': [20],
            'n_test': [10],
            'n_snapshots': [3],
            'n_features': [5],
            # Additional parameters for new benchmarks
            'n_obs': [5, 10],
            'n_rows': [50, 100],
            'n_cols': [50, 100],
            'n_ops': [100],
        }

        # Voer alle benchmarks uit met het grid
        suite.run_all(param_grid, profile_memory=args.profile_memory, filter_names=args.filter)
        logging.info(f"Benchmarks voltooid. Aantal runs: {len(suite.results)}")

        if args.save:
            suite.save_results(args.save)
            logging.info(f"Resultaten opgeslagen in {args.save}")

    if args.plot:
        suite.plot_results(x_param=args.x_param, y_metric=args.y_metric,
                           group_by=args.group_by, use_plotly=args.use_plotly)
        logging.info("Plot weergegeven.")


if __name__ == "__main__":
    main()