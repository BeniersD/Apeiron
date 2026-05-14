import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from itertools import combinations
import json
import time
import warnings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Graceful Imports of All Layer 2 Modules
# ============================================================================

_module_status = {}

def _try_import(module_name: str, class_name: Optional[str] = None):
    """Attempt to import a module and record status."""
    try:
        mod = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            return getattr(mod, class_name)
        return mod
    except ImportError:
        _module_status[module_name] = False
        return None
    except Exception:
        _module_status[module_name] = False
        return None

# Core modules (assumed present)
Hypergraph = _try_import('..hypergraph', 'Hypergraph')
if Hypergraph is None:
    try:
        from .hypergraph import Hypergraph
        _module_status['hypergraph'] = True
    except ImportError:
        _module_status['hypergraph'] = False

# Existing modules
try:
    from .relations_core import UltimateRelation, Layer2_Relational_Ultimate
    _module_status['relations_core'] = True
except ImportError:
    UltimateRelation, Layer2_Relational_Ultimate = None, None
    _module_status['relations_core'] = False

try:
    from .category import RelationalCategory, RelationalFunctor, NaturalTransformation
    _module_status['category'] = True
except ImportError:
    RelationalCategory, RelationalFunctor, NaturalTransformation = None, None, None
    _module_status['category'] = False

try:
    from .spectral import SpectralGraphAnalysis
    _module_status['spectral'] = True
except ImportError:
    SpectralGraphAnalysis = None
    _module_status['spectral'] = False

try:
    from .causal_discovery import CausalDiscovery
    _module_status['causal_discovery'] = True
except ImportError:
    CausalDiscovery = None
    _module_status['causal_discovery'] = False

try:
    from .motif_detection import MotifCounter
    _module_status['motif_detection'] = True
except ImportError:
    MotifCounter = None
    _module_status['motif_detection'] = False

try:
    from .mapper import Mapper
    _module_status['mapper'] = True
except ImportError:
    Mapper = None
    _module_status['mapper'] = False

try:
    from .quantum_graph import QuantumGraph
    _module_status['quantum_graph'] = True
except ImportError:
    QuantumGraph = None
    _module_status['quantum_graph'] = False

try:
    from .temporal_networks import TemporalGraph
    _module_status['temporal_networks'] = True
except ImportError:
    TemporalGraph = None
    _module_status['temporal_networks'] = False

# New modules (v5.1)
try:
    from .sheaf_hypergraph import SheafHypergraph
    _module_status['sheaf_hypergraph'] = True
except ImportError:
    SheafHypergraph = None
    _module_status['sheaf_hypergraph'] = False

try:
    from .categorical_tda import CategoricalTDA, PersistenceModule
    _module_status['categorical_tda'] = True
except ImportError:
    CategoricalTDA, PersistenceModule = None, None
    _module_status['categorical_tda'] = False

try:
    from .hodge_decomposition import HypergraphHodgeDecomposer
    _module_status['hodge_decomposition'] = True
except ImportError:
    HypergraphHodgeDecomposer = None
    _module_status['hodge_decomposition'] = False

try:
    from .higher_category import StrictTwoCategory, Bicategory
    _module_status['higher_category'] = True
except ImportError:
    StrictTwoCategory, Bicategory = None, None
    _module_status['higher_category'] = False

try:
    from .spectral_sheaf import SheafSpectralAnalyzer
    _module_status['spectral_sheaf'] = True
except ImportError:
    SheafSpectralAnalyzer = None
    _module_status['spectral_sheaf'] = False

try:
    from .endogenous_time import EndogenousTimeGenerator
    _module_status['endogenous_time'] = True
except ImportError:
    EndogenousTimeGenerator = None
    _module_status['endogenous_time'] = False

try:
    from .formal_layer2_verification import Layer2VerificationOrchestrator
    _module_status['formal_layer2_verification'] = True
except ImportError:
    Layer2VerificationOrchestrator = None
    _module_status['formal_layer2_verification'] = False

try:
    from .quantum_topology import QuantumBettiEstimator
    _module_status['quantum_topology'] = True
except ImportError:
    QuantumBettiEstimator = None
    _module_status['quantum_topology'] = False

# Extreme modules (v6.0)
try:
    from .sheaf_diffusion_dynamics import SheafDiffusionDynamics, DiffusionState
    _module_status['sheaf_diffusion_dynamics'] = True
except ImportError:
    SheafDiffusionDynamics, DiffusionState = None, None
    _module_status['sheaf_diffusion_dynamics'] = False

try:
    from .topos_layer2 import ToposLogic, topos_from_hypergraph
    _module_status['topos_layer2'] = True
except ImportError:
    ToposLogic, topos_from_hypergraph = None, None
    _module_status['topos_layer2'] = False

try:
    from .hott_category import UnivalentCategory, univalent_category_from_hypergraph
    _module_status['hott_category'] = True
except ImportError:
    UnivalentCategory, univalent_category_from_hypergraph = None, None
    _module_status['hott_category'] = False

try:
    from .derived_learning import ErrorPropagation, derived_learning_pipeline
    _module_status['derived_learning'] = True
except ImportError:
    ErrorPropagation, derived_learning_pipeline = None, None
    _module_status['derived_learning'] = False

try:
    from .ontogenesis_engine import OntogenesisEngine, ontogenesis_from_hypergraph
    _module_status['ontogenesis_engine'] = True
except ImportError:
    OntogenesisEngine, ontogenesis_from_hypergraph = None, None
    _module_status['ontogenesis_engine'] = False

try:
    from .retrocausal_dynamics import RetrocausalDynamics
    _module_status['retrocausal_dynamics'] = True
except ImportError:
    RetrocausalDynamics = None
    _module_status['retrocausal_dynamics'] = False

try:
    from .spectral_triple import SpectralTriple, spectral_triple_from_hypergraph
    _module_status['spectral_triple'] = True
except ImportError:
    SpectralTriple, spectral_triple_from_hypergraph = None, None
    _module_status['spectral_triple'] = False

try:
    from .epistemic_horizon import EpistemicHorizonDetector, DataQuarantine, horizon_pipeline
    _module_status['epistemic_horizon'] = True
except ImportError:
    EpistemicHorizonDetector, DataQuarantine, horizon_pipeline = None, None, None
    _module_status['epistemic_horizon'] = False

try:
    from .reaction_functor import BioDigitalCompiler, compile_hypergraph_to_gcode
    _module_status['reaction_functor'] = True
except ImportError:
    BioDigitalCompiler, compile_hypergraph_to_gcode = None, None
    _module_status['reaction_functor'] = False


# ============================================================================
# Coverage Analyzer
# ============================================================================

@dataclass
class CoverageReport:
    total_modules: int = 0
    available_modules: int = 0
    missing_modules: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0
    details: Dict[str, bool] = field(default_factory=dict)

    def __repr__(self):
        return f"CoverageReport({self.coverage_percentage:.1f}%, {self.available_modules}/{self.total_modules})"


def compute_theory_coverage() -> CoverageReport:
    required = [
        'hypergraph', 'relations_core', 'category', 'spectral',
        'causal_discovery', 'motif_detection', 'mapper', 'quantum_graph',
        'temporal_networks', 'sheaf_hypergraph', 'categorical_tda',
        'hodge_decomposition', 'higher_category', 'spectral_sheaf',
        'endogenous_time', 'formal_layer2_verification', 'quantum_topology',
        # Extreme modules
        'sheaf_diffusion_dynamics', 'topos_layer2', 'hott_category',
        'derived_learning', 'ontogenesis_engine', 'retrocausal_dynamics',
        'spectral_triple', 'epistemic_horizon', 'reaction_functor'
    ]
    available = sum(1 for mod in required if _module_status.get(mod, False))
    missing = [mod for mod in required if not _module_status.get(mod, False)]
    return CoverageReport(
        total_modules=len(required),
        available_modules=available,
        missing_modules=missing,
        coverage_percentage=100.0 * available / len(required) if required else 100.0,
        details={mod: _module_status.get(mod, False) for mod in required}
    )


# ============================================================================
# Unified API
# ============================================================================

class Layer2UnifiedAPI:
    def __init__(self, hypergraph, observables=None, config=None):
        self.hypergraph = hypergraph
        self.observables = observables or []
        self.config = config or {}
        self._report_cache = None

    def full_analysis(self, force_recompute: bool = False, block_on_failure: bool = True) -> Dict[str, Any]:
        if self._report_cache is not None and not force_recompute:
            return self._report_cache

        report = {
            'hypergraph': {
                'num_vertices': len(self.hypergraph.vertices),
                'num_edges': len(self.hypergraph.hyperedges),
                'timestamp': time.time(),
            },
            'coverage': self._compute_coverage(),
            'topology': self._run_topology(),
            'categorical': self._run_categorical(),
            'spectral': self._run_spectral(),
            'sheaf': self._run_sheaf(),
            'hodge': self._run_hodge(),
            'causal': self._run_causal(),
            'quantum': self._run_quantum(),
            'verification': self._run_verification(),
            # Extreme modules
            'sheaf_diffusion': self._run_sheaf_diffusion(),
            'topos_logic': self._run_topos_logic(),
            'hott': self._run_hott(),
            'derived_learning': self._run_derived_learning(),
            'ontogenesis': self._run_ontogenesis(),
            'retrocausal': self._run_retrocausal(),
            'spectral_triple': self._run_spectral_triple(),
            'epistemic_horizon': self._run_epistemic_horizon(),
            'reaction_functor': self._run_reaction_functor(),
        }

        # Active guard
        if block_on_failure:
            verif = report.get('verification', {})
            if verif.get('status') == 'success' and not verif.get('all_passed', True):
                report['blocked'] = True
                report['block_reason'] = (
                    'Formal verification failed: the relational constitution axiom '
                    'or another property is violated. No further relations can be formed.'
                )
                logger.critical("Layer 2 blocked due to failed formal verification.")

        self._report_cache = report
        return report

    def _warn_fallback(self, module: str, reason: str) -> Dict[str, Any]:
        msg = f"[EPISTEMIC HUMILITY] {module}: {reason}"
        warnings.warn(msg)
        return {
            'status': 'fallback',
            'warning': msg,
            'module': module,
            'reason': reason,
            'timestamp': time.time()
        }

    # ------- Basis analyses (ongewijzigd) -------
    def _compute_coverage(self) -> Dict[str, Any]:
        cr = compute_theory_coverage()
        return {
            'percentage': cr.coverage_percentage,
            'available': cr.available_modules,
            'total': cr.total_modules,
            'missing': cr.missing_modules,
        }

    def _run_topology(self) -> Dict[str, Any]:
        try:
            betti = self.hypergraph.betti_numbers() if hasattr(self.hypergraph, 'betti_numbers') else []
            persistent = None
            if hasattr(self.hypergraph, 'persistent_homology'):
                persistent = self.hypergraph.persistent_homology()
            return {
                'betti_numbers': betti,
                'persistent_homology': 'computed' if persistent is not None else 'not available',
                'status': 'success'
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    def _run_categorical(self) -> Dict[str, Any]:
        result = {'status': 'partial', 'components': {}}
        if RelationalCategory is not None:
            try:
                vertices = [f"v_{v}" for v in self.hypergraph.vertices]
                edges = []
                for edge in self.hypergraph.hyperedges:
                    for v1, v2 in combinations(edge, 2):
                        edges.append((f"v_{v1}", f"v_{v2}"))
                cat = RelationalCategory(vertices, edges)
                result['components']['category'] = 'success'
            except Exception as e:
                result['components']['category'] = f'failed: {e}'
        else:
            result['components']['category'] = 'module not available'

        if Bicategory is not None:
            try:
                vertices = [f"v_{v}" for v in self.hypergraph.vertices]
                one_morphisms = {}
                for i, edge in enumerate(self.hypergraph.hyperedges):
                    for v1, v2 in combinations(edge, 2):
                        one_morphisms[f"e_{i}_{v1}_{v2}"] = (f"v_{v1}", f"v_{v2}")
                bicat = Bicategory(vertices, one_morphisms, {})
                axioms = bicat.verify_bicategory_axioms()
                result['components']['bicategory'] = 'success'
                result['components']['bicategory_axioms'] = axioms
            except Exception as e:
                result['components']['bicategory'] = f'failed: {e}'
        else:
            result['components']['bicategory'] = 'module not available'
        return result

    def _run_spectral(self) -> Dict[str, Any]:
        if SpectralGraphAnalysis is not None:
            try:
                sga = SpectralGraphAnalysis(self.hypergraph)
                return {
                    'status': 'success',
                    'connectivity': sga.algebraic_connectivity(),
                    'eigenvalues_computed': True,
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_sheaf(self) -> Dict[str, Any]:
        if SheafHypergraph is not None:
            try:
                vertices = [f"v_{v}" for v in self.hypergraph.vertices]
                hyperedges = [{f"v_{v}" for v in edge} for edge in self.hypergraph.hyperedges]
                shg = SheafHypergraph(vertices, hyperedges)
                cohom = shg.compute_cohomology()
                result = {
                    'status': 'success',
                    'cohomology': {
                        'h0': cohom.h0_dimension,
                        'h1': cohom.h1_dimension,
                        'is_consistent': cohom.is_globally_consistent,
                    }
                }
                if SheafSpectralAnalyzer is not None:
                    try:
                        ssa = SheafSpectralAnalyzer(shg)
                        spec = ssa.compute_sheaf_spectral_invariants()
                        result['spectral'] = spec
                    except Exception:
                        pass
                return result
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_hodge(self) -> Dict[str, Any]:
        if HypergraphHodgeDecomposer is not None:
            try:
                hhd = HypergraphHodgeDecomposer(self.hypergraph)
                thm = hhd.verify_hodge_theorem(k=0)
                harmonic_basis_dim = hhd.get_harmonic_basis(0).shape[1]
                return {
                    'status': 'success',
                    'theorem_verified': thm,
                    'harmonic_dimension': harmonic_basis_dim,
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_causal(self) -> Dict[str, Any]:
        result = {'status': 'partial', 'components': {}}
        if CausalDiscovery is not None:
            result['components']['causal_discovery'] = 'module loaded'
        else:
            result['components']['causal_discovery'] = 'module not available'

        if EndogenousTimeGenerator is not None:
            try:
                edges_list = []
                for edge in self.hypergraph.hyperedges:
                    edge_list = sorted(edge)
                    for i in range(len(edge_list) - 1):
                        edges_list.append((edge_list[i], edge_list[i+1]))
                gen = EndogenousTimeGenerator(edges_list)
                ordering = gen.generate_time_ordering()
                result['components']['endogenous_time'] = 'success'
                result['components']['time_ordering'] = ordering
            except Exception as e:
                result['components']['endogenous_time'] = f'failed: {e}'
        else:
            result['components']['endogenous_time'] = 'module not available'
        return result

    def _run_quantum(self) -> Dict[str, Any]:
        if QuantumBettiEstimator is not None:
            try:
                est = QuantumBettiEstimator(self.hypergraph, backend='classical')
                qresult = est.estimate_betti_numbers()
                if qresult.simulator_used == 'classical (quantum-inspired)':
                    return self._warn_fallback(
                        'quantum_topology',
                        'Classical eigensolver used as fallback; true quantum Betti estimation requires PennyLane or Qiskit backend.'
                    )
                return {
                    'status': 'success',
                    'betti_estimates': qresult.betti_numbers,
                    'backend': qresult.simulator_used
                }
            except Exception as e:
                return self._warn_fallback('quantum_topology', f'Quantum estimation failed: {e}')
        return self._warn_fallback('quantum_topology', 'Module not available; no quantum Betti estimation possible.')

    def _run_verification(self) -> Dict[str, Any]:
        if Layer2VerificationOrchestrator is not None:
            try:
                orchestrator = Layer2VerificationOrchestrator(self.hypergraph, self.observables)
                verifications = orchestrator.run_all_verifications()
                passed = sum(1 for v in verifications if v.is_valid)
                return {
                    'status': 'success',
                    'total': len(verifications),
                    'passed': passed,
                    'all_passed': all(v.is_valid for v in verifications),
                    'properties': [
                        {'name': v.property_name, 'valid': v.is_valid}
                        for v in verifications
                    ]
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    # ------- Extreme analyses (v6.0) -------
    def _run_sheaf_diffusion(self) -> Dict[str, Any]:
        if SheafDiffusionDynamics is not None and SheafHypergraph is not None:
            try:
                vertices = [f"v_{v}" for v in self.hypergraph.vertices]
                hyperedges = [{f"v_{v}" for v in edge} for edge in self.hypergraph.hyperedges]
                shg = SheafHypergraph(vertices, hyperedges)
                sdd = SheafDiffusionDynamics(shg)
                _, final = sdd.evolve(store_trajectory=False)
                detection = sdd.detect_epistemic_gradients(final)
                return {
                    'status': 'success',
                    'final_flux_max': float(np.max(final.flux)),
                    'epistemic_singularity': detection['epistemic_singularity'],
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_topos_logic(self) -> Dict[str, Any]:
        if ToposLogic is not None:
            try:
                topos = topos_from_hypergraph(self.hypergraph)
                prop = {v: True for v in self.hypergraph.vertices}
                evaluation = topos.topos_evaluate(prop)
                return {
                    'status': 'success',
                    'truth_degree': evaluation['truth_degree'],
                    'lem_holds': evaluation['lem_holds'],
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_hott(self) -> Dict[str, Any]:
        if UnivalentCategory is not None:
            try:
                uc = univalent_category_from_hypergraph(self.hypergraph)
                n_isos = len(uc.isomorphisms)
                return {
                    'status': 'success',
                    'isomorphisms_detected': n_isos,
                    'univalence_holds': uc.univalence_axiom_holds(),
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_derived_learning(self) -> Dict[str, Any]:
        if derived_learning_pipeline is not None:
            try:
                result = derived_learning_pipeline(self.hypergraph)
                return {
                    'status': 'success',
                    'obstruction_dim': result.get('obstruction_dim', 0),
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_ontogenesis(self) -> Dict[str, Any]:
        if ontogenesis_from_hypergraph is not None:
            try:
                engine = ontogenesis_from_hypergraph(self.hypergraph)
                result = engine.check_and_evolve()
                return {
                    'status': 'success' if result['status'] == 'stable' else 'evolved',
                    'jumps_performed': result.get('jumps_performed', 0),
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_retrocausal(self) -> Dict[str, Any]:
        if RetrocausalDynamics is not None:
            try:
                rd = RetrocausalDynamics(self.hypergraph, T=5, max_iterations=50)
                trajectory = rd.optimal_trajectory()
                return {
                    'status': 'success',
                    'final_obstruction': trajectory['final_obstruction'],
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_spectral_triple(self) -> Dict[str, Any]:
        if spectral_triple_from_hypergraph is not None:
            try:
                st = spectral_triple_from_hypergraph(self.hypergraph)
                summary = st.geometry_summary()
                return {
                    'status': 'success',
                    'dimension': summary['dimension'],
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_epistemic_horizon(self) -> Dict[str, Any]:
        if horizon_pipeline is not None:
            try:
                result = horizon_pipeline(self.hypergraph)
                return {
                    'status': 'success',
                    'singularities_detected': result['singularities_detected'],
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def _run_reaction_functor(self) -> Dict[str, Any]:
        if compile_hypergraph_to_gcode is not None:
            try:
                result = compile_hypergraph_to_gcode(self.hypergraph)
                return {
                    'status': 'success',
                    'num_instructions': result['num_instructions'],
                    'verification': result['verification'],
                }
            except Exception as e:
                return {'status': 'failed', 'error': str(e)}
        return {'status': 'module not available'}

    def export_report(self, filepath: str) -> None:
        report = self.full_analysis()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    def theory_coverage_check(self) -> CoverageReport:
        return compute_theory_coverage()


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)