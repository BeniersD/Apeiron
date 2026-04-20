"""
density_field.py - Relational densities between UltimateObservables.

This module implements a field that captures the influence of neighboring
observables on an observable's identity via two complementary channels:

  1. **Resonance channel**: shared resonance-map layers, weighted by per-layer
     weights and decayed by relational distance derived from embedding similarity.
  2. **Embedding channel**: direct cosine similarity of relational embeddings,
     which provides influence even between observables that share no resonance
     layers but occupy nearby positions in the feature space.

The adjacency function A: V × V → [0, 1] that the Layer 1 theory requires is
implemented as cosine similarity of the relational embeddings stored on each
UltimateObservable. This replaces the original scalar decay constant that
treated all pairs identically regardless of their position in feature space.

Influence computation is distance-aware:
    influence ∝ decay · weight / (1 + distance)
where distance = 1 − cosine_similarity(emb_target, emb_other).

Stochastic sampling (``sample_influence``) implements the Monte Carlo protocol
described in the Layer 1 theory to estimate latent dependencies under embedding
uncertainty, without mutating the original observables.

All public mutating methods are thread-safe via an internal RLock.

Optional libraries (numpy is required; all else degrade gracefully):
    numpy   – required for embedding arithmetic and sampling.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .irreducible_unit import UltimateObservable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class InfluenceSample:
    """
    Statistical summary of a Monte Carlo influence estimate for one perspective.

    Produced by ``DensityField.sample_influence`` and contains descriptive
    statistics computed over the sampled distribution of influence values.

    Attributes:
        perspective: Observer-perspective name this sample belongs to.
        mean:        Mean influence over all Monte Carlo samples.
        std:         Standard deviation of influence over all samples.
        p5:          5th-percentile influence (lower confidence bound).
        p95:         95th-percentile influence (upper confidence bound).
        n_samples:   Number of Monte Carlo samples used.
    """

    perspective: str
    mean: float
    std: float
    p5: float
    p95: float
    n_samples: int

    def __repr__(self) -> str:
        return (
            f"InfluenceSample(perspective={self.perspective!r}, "
            f"mean={self.mean:.4f}±{self.std:.4f}, "
            f"CI=[{self.p5:.4f}, {self.p95:.4f}], "
            f"n={self.n_samples})"
        )


# ---------------------------------------------------------------------------
# DensityField
# ---------------------------------------------------------------------------

class DensityField:
    """
    A field that modulates an observable's perspective based on the relational
    density of nearby observables.

    Influence is mediated through two channels:

    **Resonance channel** (weight ``resonance_channel_weight``, default 0.7):
        Influence derived from layers that appear in both the target's and the
        other observable's resonance maps. Per-layer weights are extracted from
        the resonance data (key ``'weight'``) and the contribution is decayed
        by the relational distance between the two observables:

            layer_influence = decay · w_target · w_other / (1 + distance)

    **Embedding channel** (weight ``embedding_channel_weight``, default 0.3):
        Influence derived directly from the cosine similarity of the
        observables' relational embeddings, providing non-zero influence even
        when no resonance layers are shared but the observables are close in
        feature space:

            embedding_influence = decay · max(0, cosine_similarity)

    The combined influence per other observable is:

        total = resonance_channel_weight · resonance_influence
              + embedding_channel_weight · embedding_influence

    Influences are then aggregated per observer perspective of the influencing
    observable and stored / used in ``apply_influence``.

    All mutating public methods are protected by an internal ``threading.RLock``
    so that multiple threads may safely add/remove observables concurrently.

    Attributes:
        observables:              Dict mapping observable ID → UltimateObservable.
        influence_decay:          Base decay factor applied in both channels.
        perspective_threshold:    Minimum cumulative influence to trigger a
                                  perspective switch in ``apply_influence``.
        resonance_channel_weight: Relative weight of the resonance channel
                                  (default 0.7).
        embedding_channel_weight: Relative weight of the embedding channel
                                  (default 0.3).
    """

    def __init__(
        self,
        observables: "Optional[Dict[str, UltimateObservable]]" = None,
        influence_decay: float = 0.5,
        perspective_threshold: float = 0.5,
        resonance_channel_weight: float = 0.7,
        embedding_channel_weight: float = 0.3,
    ) -> None:
        """
        Initialize a DensityField.

        Args:
            observables:              Optional initial dict of id → observable.
                                      Convenience parameter so you can write
                                      ``DensityField({"a": obs1, "b": obs2})``.
            influence_decay:          Base scalar applied in both influence channels.
            perspective_threshold:    Minimum cumulative influence needed to switch
                                      the target's observer perspective to the
                                      dominant one in ``apply_influence``.
            resonance_channel_weight: Weight of the resonance channel in the combined
                                      influence formula (default 0.7).
            embedding_channel_weight: Weight of the embedding channel in the combined
                                      influence formula (default 0.3).
        """
        self.observables: Dict[str, UltimateObservable] = {}
        self.influence_decay = influence_decay
        self.perspective_threshold = perspective_threshold
        self.resonance_channel_weight = resonance_channel_weight
        self.embedding_channel_weight = embedding_channel_weight
        self._lock = threading.RLock()
        # Pre-populate with initial observables if provided
        if observables:
            for obs in observables.values():
                self.add_observable(obs)

    # -----------------------------------------------------------------------
    # Observable management
    # -----------------------------------------------------------------------

    def add_observable(self, obs: UltimateObservable) -> None:
        """
        Add an observable to the field.

        Args:
            obs: The UltimateObservable to register.
        """
        with self._lock:
            self.observables[obs.id] = obs
        logger.debug("Added observable %s to density field", obs.id)

    def remove_observable(self, obs_id: str) -> None:
        """
        Remove an observable from the field.

        Args:
            obs_id: ID of the observable to remove.
        """
        with self._lock:
            if obs_id in self.observables:
                del self.observables[obs_id]
                logger.debug("Removed observable %s from density field", obs_id)

    def get_observable_ids(self) -> List[str]:
        """Return a snapshot list of all observable IDs currently in the field."""
        with self._lock:
            return list(self.observables.keys())

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _embedding_similarity(
        self,
        obs_a: UltimateObservable,
        obs_b: UltimateObservable,
    ) -> float:
        """
        Compute the cosine similarity between the relational embeddings of two
        observables.

        This implements the adjacency function A: V × V → [-1, 1] required by
        the Layer 1 theory, where V is the relational embedding space.
        Positive values indicate shared directional structure; negative values
        indicate opposing structure; zero indicates orthogonality.

        Handles:
            - Empty embeddings → returns 0.0.
            - Zero-norm embeddings → returns 0.0.
            - Embeddings of different lengths → aligned to the shorter one.

        Args:
            obs_a: First observable.
            obs_b: Second observable.

        Returns:
            Cosine similarity in [-1.0, 1.0].
        """
        emb_a = obs_a.relational_embedding
        emb_b = obs_b.relational_embedding

        if len(emb_a) == 0 or len(emb_b) == 0:
            return 0.0

        # Align to shortest dimension (handles heterogeneous embedding sizes)
        min_len = min(len(emb_a), len(emb_b))
        a = np.asarray(emb_a[:min_len], dtype=float)
        b = np.asarray(emb_b[:min_len], dtype=float)

        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom < 1e-12:
            return 0.0

        return float(np.clip(np.dot(a, b) / denom, -1.0, 1.0))

    @staticmethod
    def _perturb_embedding(
        embedding: np.ndarray,
        rng: np.random.Generator,
        noise_scale: float,
    ) -> np.ndarray:
        """
        Add isotropic Gaussian noise to an embedding vector.

        Noise magnitude is expressed as a fraction of the embedding's L2 norm
        so the perturbation is scale-invariant. If the norm is near zero, a
        fixed absolute noise of ``noise_scale`` is used instead.

        The original array is never modified; a new array is always returned.

        Args:
            embedding:   Embedding to perturb.
            rng:         NumPy random generator for reproducibility.
            noise_scale: Noise standard deviation relative to the embedding norm.

        Returns:
            Perturbed copy of ``embedding``.
        """
        if len(embedding) == 0:
            return embedding.copy()

        emb = np.asarray(embedding, dtype=float)
        norm = np.linalg.norm(emb)
        std = noise_scale * norm if norm > 1e-12 else noise_scale
        return emb + rng.normal(0.0, std, size=emb.shape)

    def _compute_pairwise_influence(
        self,
        target: "UltimateObservable",
        target_embedding: "np.ndarray",
        other: "UltimateObservable",
    ) -> float:
        """
        Compute the raw combined influence of ``other`` on ``target``.

        **Temporal causality (v3.1):**
        When both observables have non-zero ``temporal_phase``, causal
        ordering is enforced: ``other`` may only influence ``target`` if
        ``other.temporal_phase <= target.temporal_phase``.  This eliminates
        backward-in-time influence and aligns with the theory's demand that
        Layer 1 respects epistemic causality.

        **Influence formula:**

            causal = 1 if t_other <= t_target else 0
            similarity = cosine(target_embedding, other.relational_embedding)
            distance   = 1 - clip(similarity, -1, 1)

            resonance_l = causal · decay · w_t · w_o / (1 + distance)
            embedding   = causal · decay · max(0, similarity)

            total = resonance_w · Σ_l resonance_l + embedding_w · embedding

        Args:
            target:           Target observable.
            target_embedding: Embedding for distance computation (may be perturbed).
            other:            Influencing observable.

        Returns:
            Non-negative combined influence ≥ 0.
        """
        # --- Temporal causality filter ---
        t_target = getattr(target, "temporal_phase", 0.0)
        t_other = getattr(other, "temporal_phase", 0.0)
        if (t_target != 0.0 or t_other != 0.0) and t_other > t_target:
            return 0.0  # Future cannot influence present

        # --- Embedding similarity and relational distance ---
        emb_other = other.relational_embedding
        if len(target_embedding) > 0 and len(emb_other) > 0:
            min_len = min(len(target_embedding), len(emb_other))
            a = target_embedding[:min_len]
            b = np.asarray(emb_other[:min_len], dtype=float)
            denom = np.linalg.norm(a) * np.linalg.norm(b)
            sim = float(np.clip(np.dot(a, b) / denom, -1.0, 1.0)) if denom > 1e-12 else 0.0
        else:
            sim = 0.0

        distance = 1.0 - sim

        # --- Resonance channel ---
        resonance_influence = 0.0
        common_layers = set(target.resonance_map.keys()) & set(other.resonance_map.keys())
        for layer in common_layers:
            target_data = target.resonance_map.get(layer, {})
            other_data = other.resonance_map.get(layer, {})
            w_t = target_data.get("weight", 1.0) if isinstance(target_data, dict) else 1.0
            w_o = other_data.get("weight", 1.0) if isinstance(other_data, dict) else 1.0
            resonance_influence += self.influence_decay * w_t * w_o / (1.0 + distance)

        # --- Embedding channel ---
        embedding_influence = self.influence_decay * max(0.0, sim)

        # --- Combined ---
        total = (
            self.resonance_channel_weight * resonance_influence
            + self.embedding_channel_weight * embedding_influence
        )
        return max(0.0, total)

    # -----------------------------------------------------------------------
    # Core public API
    # -----------------------------------------------------------------------

    def compute_influence(self, target_id: str) -> Dict[str, float]:
        """
        Compute the combined influence of all other observables on the target.

        Influence from each other observable is computed via the two-channel
        formula in ``_compute_pairwise_influence`` and then aggregated by the
        observer perspective of the influencing observable.

        Changes from original implementation:
            - Adds an **embedding channel** so that nearby observables in feature
              space contribute even without shared resonance layers.
            - **Distance-decayed resonance**: layer contributions are divided by
              (1 + relational_distance) rather than using a flat decay constant.
            - Thread-safe snapshot of the observables dict at the start.

        Args:
            target_id: ID of the target observable.

        Returns:
            Dict mapping observer-perspective names to cumulative influence
            values. Returns an empty dict if the target is not found.
        """
        with self._lock:
            if target_id not in self.observables:
                logger.warning(
                    "compute_influence: target observable %s not found in field",
                    target_id,
                )
                return {}
            target = self.observables[target_id]
            # Snapshot to avoid holding the lock during computation
            target_embedding = np.asarray(target.relational_embedding, dtype=float).copy()
            others = {k: v for k, v in self.observables.items() if k != target_id}

        influences: Dict[str, float] = {}

        for other in others.values():
            infl = self._compute_pairwise_influence(target, target_embedding, other)
            if infl <= 0.0:
                continue
            persp = other.observer_perspective
            influences[persp] = influences.get(persp, 0.0) + infl

        return influences

    def apply_influence(self, target_id: str) -> None:
        """
        Modify the target observable's observer_context based on computed
        influences and optionally switch its observer perspective.

        Steps:
            1. Call ``compute_influence`` to obtain the influence dict.
            2. Store the full dict in the target's ``observer_context`` under
               ``'density_influence'``.
            3. If the dominant perspective exceeds ``perspective_threshold`` and
               differs from the current perspective, call ``set_observer`` with
               ``{'density_shift': True}`` to switch and record the transition.
            4. Call ``_mark_stale()`` so atomicity is recalculated with the
               updated context.

        Args:
            target_id: ID of the target observable.
        """
        infl = self.compute_influence(target_id)
        if not infl:
            return

        with self._lock:
            if target_id not in self.observables:
                return
            target = self.observables[target_id]

        # Store the full influence dict in observer_context
        target.observer_context["density_influence"] = infl.copy()

        # Determine dominant perspective
        dominant_persp, dominant_val = max(infl.items(), key=lambda x: x[1])

        if (
            dominant_val > self.perspective_threshold
            and dominant_persp != target.observer_perspective
        ):
            target.set_observer(dominant_persp, context={"density_shift": True})
            logger.info(
                "Observable %s switched perspective to %r "
                "due to density influence (%.4f)",
                target_id,
                dominant_persp,
                dominant_val,
            )

        # Mark stale so atomicity recalculates with updated context
        target._mark_stale()

    def clear_influence(self, target_id: str) -> None:
        """
        Remove density influence data from the target's observer_context.

        Args:
            target_id: ID of the target observable.
        """
        with self._lock:
            if target_id not in self.observables:
                return
            target = self.observables[target_id]

        target.observer_context.pop("density_influence", None)
        target._mark_stale()
        logger.debug("Cleared density influence for %s", target_id)

    # -----------------------------------------------------------------------
    # Monte Carlo sampling (new)
    # -----------------------------------------------------------------------

    def sample_influence(
        self,
        target_id: str,
        n_samples: int = 100,
        noise_scale: float = 0.05,
        random_seed: Optional[int] = None,
    ) -> Dict[str, InfluenceSample]:
        """
        Monte Carlo estimation of the influence distribution under embedding
        uncertainty.

        The target observable's relational embedding is perturbed with
        isotropic Gaussian noise for each sample and influence is recomputed,
        yielding a distribution of values per observer perspective. This
        implements the stochastic sampling protocol required by the Layer 1
        theory to explore latent dependencies that cannot be identified
        deterministically.

        The original observable is **never mutated**; all perturbations are
        applied to temporary copies of the embedding.

        Args:
            target_id:   ID of the target observable.
            n_samples:   Number of Monte Carlo samples (default: 100). Higher
                         values give tighter confidence intervals at increased
                         cost.
            noise_scale: Standard deviation of embedding perturbations expressed
                         as a fraction of the embedding's L2 norm (default:
                         0.05 = 5 %). Values above 0.2 explore wide uncertainty
                         regions; values below 0.01 approximate the deterministic
                         result.
            random_seed: Optional integer seed for reproducibility. If None, a
                         random seed is chosen by NumPy.

        Returns:
            Dict mapping perspective names to ``InfluenceSample`` dataclasses
            containing mean, std, and 5th / 95th percentiles of the sampled
            influence distribution. Returns an empty dict if the target is not
            found or if there are no other observables in the field.
        """
        with self._lock:
            if target_id not in self.observables:
                logger.warning(
                    "sample_influence: target %s not found in field", target_id
                )
                return {}
            target = self.observables[target_id]
            base_embedding = np.asarray(
                target.relational_embedding, dtype=float
            ).copy()
            others = {k: v for k, v in self.observables.items() if k != target_id}

        if not others:
            return {}

        rng = np.random.default_rng(random_seed)
        # Accumulate per-perspective samples: {perspective: [val_1, val_2, ...]}
        accumulated: Dict[str, List[float]] = {}

        for _ in range(n_samples):
            perturbed = self._perturb_embedding(base_embedding, rng, noise_scale)

            # Compute influence for this perturbed embedding
            sample_infl: Dict[str, float] = {}
            for other in others.values():
                infl = self._compute_pairwise_influence(target, perturbed, other)
                if infl <= 0.0:
                    continue
                persp = other.observer_perspective
                sample_infl[persp] = sample_infl.get(persp, 0.0) + infl

            for persp, val in sample_infl.items():
                accumulated.setdefault(persp, []).append(val)

        # Build InfluenceSample objects from the accumulated distributions
        result: Dict[str, InfluenceSample] = {}
        for persp, vals in accumulated.items():
            arr = np.asarray(vals, dtype=float)
            result[persp] = InfluenceSample(
                perspective=persp,
                mean=float(np.mean(arr)),
                std=float(np.std(arr)),
                p5=float(np.percentile(arr, 5)),
                p95=float(np.percentile(arr, 95)),
                n_samples=n_samples,
            )

        logger.debug(
            "sample_influence: %d samples for %s → %d active perspectives",
            n_samples,
            target_id,
            len(result),
        )
        return result

    # -----------------------------------------------------------------------
    # Global analysis helpers (new)
    # -----------------------------------------------------------------------

    def compute_influence_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """
        Compute the full pairwise influence matrix over all observables.

        Entry ``[i, j]`` is the influence of observable ``j`` on observable
        ``i`` (how much ``j`` shapes ``i``'s perspective). The diagonal is
        zero (self-influence is undefined).

        Useful for global topology analysis: identifying dominant nodes,
        detecting influence clusters, and producing visualisations of the
        field's relational structure.

        Returns:
            Tuple ``(matrix, ids)`` where:
                - ``matrix``: float array of shape (N, N).
                - ``ids``:    list of observable IDs in row/column order.
        """
        with self._lock:
            ids = list(self.observables.keys())
            obs_snapshot = [self.observables[k] for k in ids]

        n = len(ids)
        matrix = np.zeros((n, n), dtype=float)

        for i, target in enumerate(obs_snapshot):
            target_embedding = np.asarray(
                target.relational_embedding, dtype=float
            )
            for j, other in enumerate(obs_snapshot):
                if i == j:
                    continue
                matrix[i, j] = self._compute_pairwise_influence(
                    target, target_embedding, other
                )

        return matrix, ids

    def get_top_influencers(
        self,
        target_id: str,
        n: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        Return the top-N observables with the highest direct influence on the
        target, regardless of their observer perspective.

        Unlike ``compute_influence`` (which aggregates by perspective), this
        method returns individual observable IDs ranked by raw influence
        value. Useful for introspection, debugging, and explaining why a
        perspective switch occurred.

        Args:
            target_id: ID of the target observable.
            n:         Maximum number of influencers to return (default: 5).

        Returns:
            List of ``(observable_id, influence_value)`` tuples sorted
            descending by influence. Returns an empty list if the target is
            not found or if there are no other observables.
        """
        with self._lock:
            if target_id not in self.observables:
                logger.warning(
                    "get_top_influencers: target %s not found in field", target_id
                )
                return []
            target = self.observables[target_id]
            target_embedding = np.asarray(
                target.relational_embedding, dtype=float
            ).copy()
            others = {k: v for k, v in self.observables.items() if k != target_id}

        scores: List[Tuple[str, float]] = []
        for other_id, other in others.items():
            infl = self._compute_pairwise_influence(target, target_embedding, other)
            scores.append((other_id, infl))

        scores.sort(key=lambda pair: pair[1], reverse=True)
        return scores[:n]

    def apply_influence_all(self) -> None:
        """
        Apply influence to every observable currently in the field.

        Convenience method that calls ``apply_influence`` for each observable.
        Observables are processed in a fixed order derived from a snapshot of
        the current IDs to avoid issues with concurrent additions.
        """
        with self._lock:
            ids = list(self.observables.keys())

        for obs_id in ids:
            self.apply_influence(obs_id)

    # -----------------------------------------------------------------------
    # Dunder
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"DensityField("
            f"observables={len(self.observables)}, "
            f"decay={self.influence_decay}, "
            f"threshold={self.perspective_threshold}, "
            f"resonance_w={self.resonance_channel_weight}, "
            f"embedding_w={self.embedding_channel_weight})"
        )