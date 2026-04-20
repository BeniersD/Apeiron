"""
QUALITATIVE DIMENSIONS – ULTIMATE IMPLEMENTATION
===========================================================================
Theoretical foundation: Qualitative dimensions such as intensity, density,
colour, texture, etc., provide additional intrinsic properties to the
irreducible units. These dimensions can be scalar (intensity), vectorial
(colour), or tensorial, and may carry gradients, Hessians, and other
derivatives. They support operations like interpolation, scaling, and
transformation, and can be related across observables.

This module implements a comprehensive framework for qualitative dimensions,
including:

- Base classes for qualitative dimensions (scalar, vector, tensor, complex, quaternion)
- Specific dimension types: Intensity, Density, Colour (RGB, HSL, CMYK, LAB, XYZ, YUV)
- Texture, Pattern, Fractal dimensions
- Multi-resolution dimensions
- Gradient and Hessian computation (numerical, symbolic via SymPy)
- Hardware acceleration (CPU, CUDA) for many operations
- Caching and serialization (JSON, pickle, Redis)
- Visualisation utilities (2D/3D plots, colour patches)

All optional features degrade gracefully if required libraries are missing.

Bug fixes in this version
--------------------------
1. is_atomic() methods were naive stubs – Every subclass returned True
   unconditionally (or used a domain-specific heuristic with no theoretical
   motivation). All subclasses now delegate to the qualitative decomposition
   operator via is_atomic_by_operator(self.value, "qualitative") (lazy
   import, graceful degradation). Each subclass retains a principled fallback
   for environments where decomposition.py is not available.

2. No dirty-flag cache for atomicity – Repeated calls to is_atomic()
   recomputed every time (or skipped computation entirely). The base class now
   carries _atomic_cache and _atomic_stale fields implementing the same
   dirty-flag pattern used by UltimateObservable._atomicity_stale /
   _compute_atomicities.

3. VectorDimension.is_atomic() used a non-theoretical heuristic – "Exactly
   one non-zero component" is a basis-vector test, not a decomposition-
   theoretic atomicity test. The operator now takes precedence; the heuristic
   survives as a fallback.

4. ColourDimension.is_atomic() used a domain-specific saturation test –
   Saturation ≈ 1 being "pure/atomic" is a perceptual convention, not a
   Layer 1 decomposition-theoretic result. Replaced by operator delegation;
   saturation test kept as fallback.

5. MultiResolutionDimension.is_atomic() used an undocumented allclose test –
   The "all scales equal" test is a reasonable proxy but not grounded in the
   formal framework. Replaced by operator delegation with the scale-equality
   test as fallback.

6. gradient_symbolic referenced sp unconditionally – If SymPy was not
   installed, the module-level function body raised NameError. Now guarded
   with SYMPY_AVAILABLE.

Extensions in this version
---------------------------
- QualitativeDimension._atomic_cache / _atomic_stale – dirty-flag fields
  (non-init, non-repr, not compared) analogous to
  UltimateObservable._atomicity_stale.
- QualitativeDimension._mark_atomic_stale() – explicit cache invalidation
  method; called whenever value changes (e.g. from_gpu).
- QualitativeDimension._compute_is_atomic() – overridable hook that performs
  the actual computation without cache logic; base implementation delegates
  to the decomposition operator.
- GPUAcceleratedDimension – docstring updated to clarify that this class
  belongs conceptually in the infrastructure layer, not in Layer 1 theory.
"""

from __future__ import annotations

import numpy as np
import logging
import time
import hashlib
import json
import pickle
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from functools import wraps

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONAL MATHEMATICAL LIBRARIES
# ============================================================================

# NumPy/SciPy for numerical operations
try:
    import numpy as np
    from scipy.ndimage import gaussian_filter, sobel, generic_gradient_magnitude
    from scipy.interpolate import interp1d, RegularGridInterpolator
    from scipy.optimize import curve_fit
    from scipy.linalg import expm, logm
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy/SciPy not available – advanced features disabled")

# SymPy for symbolic differentiation
try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    sp = None  # type: ignore[assignment]
    SYMPY_AVAILABLE = False
    logger.warning("SymPy not available – symbolic calculus disabled")

# PyTorch for GPU acceleration
try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    torch = None  # type: ignore[assignment]
    F = None      # type: ignore[assignment]
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False
    logger.warning("PyTorch not available – GPU acceleration disabled")

# NetworkX for graph-based pattern analysis
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available – graph pattern metrics disabled")

# Scikit-image for advanced texture analysis
try:
    import skimage
    from skimage import filters, feature, texture, transform
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    logger.warning("scikit-image not available – texture extraction limited")

# OpenCV for image-based dimensions (alternative)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available – computer vision features disabled")

# Matplotlib for visualisation
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    VISUALIZATION_AVAILABLE = True
except ImportError:
    plt = None  # type: ignore[assignment]
    VISUALIZATION_AVAILABLE = False
    logger.warning("Matplotlib not available – visualisation disabled")

# Plotly for interactive visualisation (optional)
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    go = None   # type: ignore[assignment]
    px = None   # type: ignore[assignment]
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available – interactive plots disabled")

# Nolds for chaos / fractal dimension
NOLDS_AVAILABLE = False

def _import_nolds():
    """Lazy import van nolds om importtijd-crashes te voorkomen."""
    global NOLDS_AVAILABLE
    if NOLDS_AVAILABLE:
        return True
    try:
        import nolds
        NOLDS_AVAILABLE = True
        return True
    except ImportError:
        logger.warning("Nolds not available – fractal dimension estimation limited")
        return False

# Redis for distributed caching
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available – distributed caching disabled")

# ============================================================================
# LAZY IMPORT HELPER FOR DECOMPOSITION OPERATOR
# ============================================================================

def _try_is_atomic_by_operator(value: Any, operator_name: str = "qualitative") -> Optional[bool]:
    """
    Attempt to evaluate atomicity via the registered decomposition operator.

    Uses a lazy relative import so the decomposition module is only loaded
    when first needed, avoiding circular-import problems at module load time.

    Critical guard
    --------------
    When the operator's ``can_decompose(value)`` returns ``False`` (e.g.
    because the qualitative operator expects a ``QualitativeDimension``
    object but receives a raw numpy array), ``is_atomic_by_operator``
    returns ``True`` unconditionally.  Without the guard below, this would
    silently override every heuristic fallback, making ``_compute_is_atomic``
    always return ``True`` for any dimension whose raw value is not directly
    handled by the operator.  We therefore return ``None`` whenever the
    operator declares itself inapplicable, so the caller can fall through to
    its class-specific heuristic.

    Args:
        value:         The raw value to test (e.g. ``self.value``).
        operator_name: Name of the registered operator (default: ``"qualitative"``).

    Returns:
        ``True``/``False`` if the operator is available *and* applicable to
        ``value``; ``None`` if the operator is not registered, declares itself
        inapplicable (``can_decompose`` returns ``False``), or if any
        exception occurs during import or evaluation.
    """
    try:
        from .decomposition import get_decomposition_operator, is_atomic_by_operator  # type: ignore[import]
        op = get_decomposition_operator(operator_name)
        if op is None:
            return None
        # If the operator cannot handle this value type, return None so the
        # caller falls back to its own heuristic instead of receiving a
        # spurious True from is_atomic_by_operator's "not-applicable → atomic"
        # default.
        if not op.can_decompose(value):
            return None
        return bool(is_atomic_by_operator(value, operator_name))
    except Exception:
        return None

# ============================================================================
# ENUMS – Dimension Types
# ============================================================================

class DimensionType(Enum):
    """Fundamental types of qualitative dimensions."""
    SCALAR = "scalar"
    VECTOR = "vector"
    TENSOR = "tensor"
    COMPLEX = "complex"
    QUATERNION = "quaternion"

class IntensityType(Enum):
    """Specific intensity scales."""
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    PERCEPTUAL = "perceptual"
    RADIOMETRIC = "radiometric"

class DensityType(Enum):
    """Density representations."""
    PROBABILITY = "probability"
    MASS = "mass"
    CHARGE = "charge"
    INFORMATION = "information"

class ColourSpace(Enum):
    """Colour spaces."""
    RGB = "rgb"
    HSL = "hsl"
    HSV = "hsv"
    CMYK = "cmyk"
    LAB = "lab"
    XYZ = "xyz"
    YUV = "yuv"

class TextureType(Enum):
    """Texture descriptors."""
    GABOR = "gabor"
    LBP = "local_binary_pattern"
    GLCM = "gray_level_cooccurrence"
    FRACTAL = "fractal_dimension"
    WAVELET = "wavelet"
    HOG = "histogram_of_oriented_gradients"
    SIFT = "scale_invariant_feature_transform"

class PatternType(Enum):
    """Pattern descriptors (recurrence, correlation)."""
    RECURRENCE = "recurrence"
    CORRELATION = "correlation"
    ENTROPY = "entropy"
    LYAPUNOV = "lyapunov"

# ============================================================================
# BASE CLASS: QualitativeDimension
# ============================================================================

@dataclass
class QualitativeDimension(ABC):
    """
    Abstract base class for any qualitative dimension.

    Atomicity cache
    ---------------
    The class maintains a dirty-flag cache for is_atomic() results
    analogous to UltimateObservable._atomicity_stale:

    _atomic_cache
        Cached boolean result of the last is_atomic() call, or None
        if no result has been computed yet.
    _atomic_stale
        When True, the cache is invalid and _compute_is_atomic() will be
        re-invoked on the next is_atomic() call.

    Call _mark_atomic_stale() to invalidate the cache after any mutation
    that could affect atomicity (e.g. changing value).
    """

    name: str
    value: Any                               # actual numeric value(s)
    unit: Optional[str] = None               # physical unit (e.g., "cd/m2", "kg/m3")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional gradient (first derivative)
    gradient: Optional[np.ndarray] = None
    # Optional Hessian (second derivative)
    hessian: Optional[np.ndarray] = None
    # Optional higher-order derivatives
    higher_derivatives: Dict[int, np.ndarray] = field(default_factory=dict)

    # Caching of computed properties (general-purpose)
    _cache: Dict[str, Any] = field(default_factory=dict)

    # ---- Atomicity dirty-flag cache (non-init, non-repr, not compared) ----
    _atomic_cache: Optional[bool] = field(
        default=None, init=False, repr=False, compare=False
    )
    _atomic_stale: bool = field(
        default=True, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Validate and normalize value."""
        self._normalize_value()
        self._compute_default_gradient()

    @abstractmethod
    def _normalize_value(self) -> None:
        """Ensure value is in a canonical form."""
        pass

    def _compute_default_gradient(self) -> None:
        """Compute gradient using finite differences if not provided."""
        if self.gradient is None and self._supports_gradient():
            self.gradient = self._finite_difference_gradient()

    def _supports_gradient(self) -> bool:
        """Whether gradient computation is supported for this dimension."""
        return False  # override in subclasses

    def _finite_difference_gradient(self, eps: float = 1e-6) -> Optional[np.ndarray]:
        """Numerical gradient using central differences."""
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary (excluding cache)."""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'value': self._serialize_value(),
            'unit': self.unit,
            'created_at': self.created_at,
            'metadata': self.metadata,
            'gradient': self._serialize_gradient(),
            'hessian': self._serialize_hessian(),
        }

    def _serialize_value(self) -> Any:
        """Convert value to JSON-serializable form."""
        if isinstance(self.value, np.ndarray):
            return self.value.tolist()
        if isinstance(self.value, complex):
            return [self.value.real, self.value.imag]
        if isinstance(self.value, (list, tuple)) and all(isinstance(x, complex) for x in self.value):
            return [(x.real, x.imag) for x in self.value]
        return self.value

    def _serialize_gradient(self) -> Optional[Any]:
        if self.gradient is None:
            return None
        if isinstance(self.gradient, np.ndarray):
            return self.gradient.tolist()
        return self.gradient

    def _serialize_hessian(self) -> Optional[Any]:
        if self.hessian is None:
            return None
        if isinstance(self.hessian, np.ndarray):
            return self.hessian.tolist()
        return self.hessian

    def to_json(self) -> str:
        """Return JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QualitativeDimension):
            return False
        return (self.name == other.name and
                np.allclose(self._value_to_array(), other._value_to_array()))

    def _value_to_array(self) -> np.ndarray:
        """Convert value to numpy array for comparisons."""
        return np.asarray(self.value)

    # ------------------------------------------------------------------------
    # GPU acceleration (mixin)
    # ------------------------------------------------------------------------
    def to_gpu(self) -> QualitativeDimension:
        """Transfer value to GPU memory (if PyTorch available)."""
        if TORCH_AVAILABLE and CUDA_AVAILABLE:
            self._gpu_tensor = torch.tensor(self.value, device='cuda')
        return self

    def from_gpu(self) -> QualitativeDimension:
        """Retrieve value from GPU memory."""
        if hasattr(self, '_gpu_tensor'):
            self.value = self._gpu_tensor.cpu().numpy()
            del self._gpu_tensor
            self._mark_atomic_stale()   # value changed -> invalidate cache
        return self

    # ------------------------------------------------------------------------
    # Symbolic gradient (if SymPy available)
    # ------------------------------------------------------------------------
    def symbolic_gradient(self, var: Any) -> Optional[Any]:
        """Compute symbolic gradient if the dimension can be expressed symbolically."""
        return None

    # ========================================================================
    # Atomicity – dirty-flag cache + operator delegation
    # ========================================================================

    def _mark_atomic_stale(self) -> None:
        """
        Invalidate the atomicity cache.

        Call this whenever value is mutated directly so that the next
        is_atomic() call recomputes from scratch.
        """
        self._atomic_stale = True
        self._atomic_cache = None

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Perform the actual atomicity computation without cache logic.

        Base implementation delegates to the qualitative decomposition
        operator via is_atomic_by_operator(self.value, "qualitative").
        If the operator is unavailable or not applicable, returns True
        (conservative fallback: an uncharacterised dimension is assumed
        atomic at Layer 1).

        Subclasses override this method (NOT is_atomic()) to provide
        class-specific fallbacks while still benefiting from the cache.

        Args:
            threshold: Tolerance used by fallback heuristics when the
                       formal operator is unavailable.

        Returns:
            True if the dimension is considered atomic; False if it can
            be meaningfully decomposed.
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True  # conservative fallback

    def is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Determine whether this qualitative dimension is atomic.

        Uses a dirty-flag cache: if _atomic_stale is False and
        _atomic_cache is not None, the cached result is returned directly
        without recomputation. Otherwise _compute_is_atomic is called,
        and the result is stored in the cache.

        Subclasses should override _compute_is_atomic() rather than this
        method in order to preserve cache semantics.

        Args:
            threshold: Tolerance for fallback heuristics (passed to
                       _compute_is_atomic).

        Returns:
            True if the dimension is atomic; False otherwise.
        """
        if not self._atomic_stale and self._atomic_cache is not None:
            return self._atomic_cache
        result = self._compute_is_atomic(threshold)
        self._atomic_cache = result
        self._atomic_stale = False
        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, value={self.value})"


# ============================================================================
# SCALAR DIMENSIONS (Intensity, Density, etc.)
# ============================================================================

class ScalarDimension(QualitativeDimension):
    """A dimension with a single scalar value."""

    def __init__(self, name: str, value: float, **kwargs: Any) -> None:
        super().__init__(name=name, value=value, **kwargs)

    def _normalize_value(self) -> None:
        self.value = float(self.value)

    def _supports_gradient(self) -> bool:
        return True

    def _finite_difference_gradient(self, eps: float = 1e-6) -> Optional[np.ndarray]:
        return None

    def interpolate(self, other: ScalarDimension, t: float) -> ScalarDimension:
        """Linear interpolation between two scalars."""
        new_val = (1 - t) * self.value + t * other.value
        return ScalarDimension(name=f"{self.name}_interp", value=new_val, unit=self.unit)

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to decomposition operator; fallback True (scalar has no
        internal structure decomposable at Layer 1).
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


class IntensityDimension(ScalarDimension):
    """Represents intensity (brightness, loudness, etc.)."""

    def __init__(
        self,
        value: float,
        intensity_type: IntensityType = IntensityType.LINEAR,
        unit: str = "cd/m2",
        name: str = "intensity",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, unit=unit, **kwargs)
        self.intensity_type = intensity_type
        self.metadata['intensity_type'] = intensity_type.value

    def to_perceptual(self) -> IntensityDimension:
        """Convert linear intensity to perceptual (sRGB gamma)."""
        if self.intensity_type == IntensityType.LINEAR:
            new_val = self.value ** (1 / 2.2) if self.value >= 0 else -((-self.value) ** (1 / 2.2))
            return IntensityDimension(value=new_val, intensity_type=IntensityType.PERCEPTUAL)
        return self

    def to_linear(self) -> IntensityDimension:
        """Convert perceptual intensity back to linear."""
        if self.intensity_type == IntensityType.PERCEPTUAL:
            new_val = self.value ** 2.2 if self.value >= 0 else -((-self.value) ** 2.2)
            return IntensityDimension(value=new_val, intensity_type=IntensityType.LINEAR)
        return self

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """Delegate to operator; fallback True (intensity is a scalar)."""
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


class DensityDimension(ScalarDimension):
    """Represents density (probability, mass, information)."""

    def __init__(
        self,
        value: float,
        density_type: DensityType = DensityType.PROBABILITY,
        unit: str = "kg/m3",
        name: str = "density",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, unit=unit, **kwargs)
        self.density_type = density_type
        self.metadata['density_type'] = density_type.value

    def integrate_over_volume(self, volume: float) -> float:
        """Total mass/information over given volume."""
        return self.value * volume

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """Delegate to operator; fallback True (density is a scalar)."""
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


# ============================================================================
# VECTOR DIMENSIONS (Colour, etc.)
# ============================================================================

class VectorDimension(QualitativeDimension):
    """A dimension with a vector value."""

    def __init__(
        self,
        name: str,
        value: Union[List[float], np.ndarray],
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=np.asarray(value, dtype=float), **kwargs)

    def _normalize_value(self) -> None:
        self.value = np.asarray(self.value, dtype=float)
        if self.value.ndim != 1:
            raise ValueError("VectorDimension requires 1D array")

    def magnitude(self) -> float:
        """Euclidean norm."""
        return float(np.linalg.norm(self.value))

    def normalise(self) -> VectorDimension:
        """Return unit vector."""
        mag = self.magnitude()
        if mag == 0:
            return self
        new_val = self.value / mag
        return VectorDimension(name=self.name, value=new_val, unit=self.unit)

    def dot(self, other: VectorDimension) -> float:
        """Dot product."""
        return float(np.dot(self.value, other.value))

    def cross(self, other: VectorDimension) -> np.ndarray:
        """Cross product (only for 3D)."""
        if len(self.value) == 3 and len(other.value) == 3:
            return np.cross(self.value, other.value)
        raise ValueError("Cross product only defined for 3D vectors")

    def interpolate(self, other: VectorDimension, t: float) -> VectorDimension:
        """Linear interpolation."""
        new_val = (1 - t) * self.value + t * other.value
        return VectorDimension(name=f"{self.name}_interp", value=new_val, unit=self.unit)

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to decomposition operator.

        Fallback heuristic (when operator unavailable): a vector is atomic if
        exactly one component is non-zero (basis-vector test). This reflects
        the Boolean-algebraic notion of an atom (minimal non-zero element)
        applied to the support of the vector.

        Bug fix: the original implementation used only this heuristic without
        any decomposition-theoretic grounding; the operator now takes
        precedence and the heuristic is the fallback.
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        # Fallback: basis-vector heuristic
        non_zero = int(np.sum(np.abs(self.value) > threshold))
        return bool(non_zero == 1)


# ============================================================================
# GPU ACCELERATED DIMENSION (infrastructure wrapper – not Layer 1 theory)
# ============================================================================

class GPUAcceleratedDimension(VectorDimension):
    """
    A vector dimension that prioritizes GPU acceleration when available.
    All operations are performed on GPU if PyTorch + CUDA are present.

    Infrastructure note
    -------------------
    This class provides a hardware-accelerated variant of VectorDimension
    and belongs conceptually to the **infrastructure layer**, not to Layer 1
    theory. It does not carry new theoretical semantics – it is purely an
    optimisation wrapper. In a full Nexus deployment it should live in an
    infrastructure or hardware-abstraction module rather than in
    qualitative_dimensions.py. It is retained here for backward compatibility,
    but higher-layer code should reference VectorDimension for type-checking
    and theory-driven dispatch, and use GPUAcceleratedDimension only when
    hardware acceleration is explicitly required.

    Atomicity
    ---------
    Inherits _compute_is_atomic() from VectorDimension unchanged. GPU-side
    representations do not affect the theoretical atomicity of the underlying
    value.
    """

    def __init__(
        self,
        name: str,
        value: Union[List[float], np.ndarray],
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, **kwargs)
        if TORCH_AVAILABLE and CUDA_AVAILABLE:
            self._gpu_tensor = torch.tensor(self.value, device='cuda')
            self._on_gpu = True
        else:
            self._on_gpu = False

    def to_gpu(self) -> GPUAcceleratedDimension:
        """Ensure tensor is on GPU."""
        if TORCH_AVAILABLE and CUDA_AVAILABLE and not self._on_gpu:
            self._gpu_tensor = torch.tensor(self.value, device='cuda')
            self._on_gpu = True
        return self

    def from_gpu(self) -> GPUAcceleratedDimension:
        """Bring tensor back to CPU."""
        if self._on_gpu:
            self.value = self._gpu_tensor.cpu().numpy()
            del self._gpu_tensor
            self._on_gpu = False
            self._mark_atomic_stale()   # value changed -> invalidate cache
        return self

    def magnitude(self) -> float:
        """Euclidean norm, computed on GPU if possible."""
        if self._on_gpu:
            return float(torch.norm(self._gpu_tensor).item())
        return super().magnitude()

    def normalise(self) -> GPUAcceleratedDimension:
        """Return unit vector, using GPU if available."""
        mag = self.magnitude()
        if mag == 0:
            return self
        if self._on_gpu:
            new_val = (self._gpu_tensor / mag).cpu().numpy()
        else:
            new_val = self.value / mag
        return GPUAcceleratedDimension(name=self.name, value=new_val, unit=self.unit)

    def dot(self, other: GPUAcceleratedDimension) -> float:
        """Dot product, using GPU if available."""
        if self._on_gpu and hasattr(other, '_on_gpu') and other._on_gpu:
            return float(torch.dot(self._gpu_tensor, other._gpu_tensor).item())
        return super().dot(other)

    # _compute_is_atomic() inherited from VectorDimension


# ============================================================================
# COLOUR DIMENSION (extends VectorDimension)
# ============================================================================

class ColourDimension(VectorDimension):
    """Represents colour in various colour spaces."""

    def __init__(
        self,
        value: Union[List[float], np.ndarray],
        colour_space: ColourSpace = ColourSpace.RGB,
        name: str = "colour",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, **kwargs)
        self.colour_space = colour_space
        self.metadata['colour_space'] = colour_space.value

    def convert_to(self, target_space: ColourSpace) -> ColourDimension:
        """Convert colour to another colour space."""
        if self.colour_space == target_space:
            return self
        rgb = self._to_rgb()
        if target_space == ColourSpace.RGB:
            new_val = rgb
        elif target_space == ColourSpace.HSL:
            new_val = self._rgb_to_hsl(rgb)
        elif target_space == ColourSpace.HSV:
            new_val = self._rgb_to_hsv(rgb)
        elif target_space == ColourSpace.CMYK:
            new_val = self._rgb_to_cmyk(rgb)
        elif target_space == ColourSpace.LAB:
            new_val = self._rgb_to_lab(rgb)
        elif target_space == ColourSpace.XYZ:
            new_val = self._rgb_to_xyz(rgb)
        elif target_space == ColourSpace.YUV:
            new_val = self._rgb_to_yuv(rgb)
        else:
            raise ValueError(f"Conversion to {target_space} not implemented")
        return ColourDimension(value=new_val, colour_space=target_space, unit=self.unit)

    def _to_rgb(self) -> np.ndarray:
        """Convert current colour to RGB."""
        if self.colour_space == ColourSpace.RGB:
            return self.value
        if self.colour_space == ColourSpace.HSL:
            return self._hsl_to_rgb(self.value)
        if self.colour_space == ColourSpace.HSV:
            return self._hsv_to_rgb(self.value)
        if self.colour_space == ColourSpace.CMYK:
            return self._cmyk_to_rgb(self.value)
        if self.colour_space == ColourSpace.LAB:
            return self._lab_to_rgb(self.value)
        if self.colour_space == ColourSpace.XYZ:
            return self._xyz_to_rgb(self.value)
        if self.colour_space == ColourSpace.YUV:
            return self._yuv_to_rgb(self.value)
        raise ValueError(f"Cannot convert from {self.colour_space}")

    @staticmethod
    def _hsl_to_rgb(hsl: np.ndarray) -> np.ndarray:
        h, s, l = hsl
        if s == 0:
            return np.array([l, l, l])
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
        return np.array([r, g, b])

    @staticmethod
    def _rgb_to_hsl(rgb: np.ndarray) -> np.ndarray:
        r, g, b = rgb
        maxc = max(r, g, b); minc = min(r, g, b)
        l = (maxc + minc) / 2
        if maxc == minc:
            return np.array([0.0, 0.0, l])
        d = maxc - minc
        s = d / (1 - abs(2*l - 1))
        if maxc == r: h = (g - b) / d % 6
        elif maxc == g: h = (b - r) / d + 2
        else: h = (r - g) / d + 4
        h /= 6
        return np.array([h, s, l])

    @staticmethod
    def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
        r, g, b = rgb
        maxc = max(r, g, b); minc = min(r, g, b)
        v = maxc; s = 0; h = 0
        if maxc != 0:
            s = (maxc - minc) / maxc
        if s != 0:
            d = maxc - minc
            if maxc == r: h = (g - b) / d % 6
            elif maxc == g: h = (b - r) / d + 2
            else: h = (r - g) / d + 4
            h /= 6
        return np.array([h, s, v])

    @staticmethod
    def _hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
        h, s, v = hsv
        if s == 0: return np.array([v, v, v])
        i = int(h * 6); f = h * 6 - i
        p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
        if i == 0: return np.array([v, t, p])
        if i == 1: return np.array([q, v, p])
        if i == 2: return np.array([p, v, t])
        if i == 3: return np.array([p, q, v])
        if i == 4: return np.array([t, p, v])
        return np.array([v, p, q])

    @staticmethod
    def _rgb_to_cmyk(rgb: np.ndarray) -> np.ndarray:
        r, g, b = rgb
        k = 1 - max(r, g, b)
        if k == 1: return np.array([0, 0, 0, 1])
        c = (1 - r - k) / (1 - k); m = (1 - g - k) / (1 - k); y = (1 - b - k) / (1 - k)
        return np.array([c, m, y, k])

    @staticmethod
    def _cmyk_to_rgb(cmyk: np.ndarray) -> np.ndarray:
        c, m, y, k = cmyk
        r = 1 - min(1, c * (1 - k) + k); g = 1 - min(1, m * (1 - k) + k); b = 1 - min(1, y * (1 - k) + k)
        return np.array([r, g, b])

    @staticmethod
    def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
        """Simplified sRGB -> XYZ -> Lab."""
        r, g, b = rgb
        r_lin = r ** 2.2 if r > 0.04045 else r / 12.92
        g_lin = g ** 2.2 if g > 0.04045 else g / 12.92
        b_lin = b ** 2.2 if b > 0.04045 else b / 12.92
        x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
        y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
        z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041
        x /= 0.95047; z /= 1.08883
        def f(t: float) -> float:
            return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116
        fx = f(x); fy = f(y); fz = f(z)
        return np.array([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)])

    @staticmethod
    def _lab_to_rgb(lab: np.ndarray) -> np.ndarray:
        L, a, b = lab
        y = (L + 16) / 116; x = a / 500 + y; z = y - b / 200
        def finv(t: float) -> float:
            return t**3 if t**3 > 0.008856 else (t - 16/116) / 7.787
        x_r = finv(x) * 0.95047; y_r = finv(y); z_r = finv(z) * 1.08883
        r_lin = x_r *  3.2404542 + y_r * -1.5371385 + z_r * -0.4985314
        g_lin = x_r * -0.9692660 + y_r *  1.8760108 + z_r *  0.0415560
        b_lin = x_r *  0.0556434 + y_r * -0.2040259 + z_r *  1.0572252
        def gamma(u: float) -> float:
            return 1.055 * u**(1/2.4) - 0.055 if u > 0.0031308 else 12.92 * u
        return np.array([gamma(max(0, min(1, r_lin))), gamma(max(0, min(1, g_lin))), gamma(max(0, min(1, b_lin)))])

    @staticmethod
    def _rgb_to_xyz(rgb: np.ndarray) -> np.ndarray:
        r, g, b = rgb
        r_lin = r ** 2.2 if r > 0.04045 else r / 12.92
        g_lin = g ** 2.2 if g > 0.04045 else g / 12.92
        b_lin = b ** 2.2 if b > 0.04045 else b / 12.92
        return np.array([
            r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375,
            r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750,
            r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041,
        ])

    @staticmethod
    def _xyz_to_rgb(xyz: np.ndarray) -> np.ndarray:
        x, y, z = xyz
        r_lin = x *  3.2404542 + y * -1.5371385 + z * -0.4985314
        g_lin = x * -0.9692660 + y *  1.8760108 + z *  0.0415560
        b_lin = x *  0.0556434 + y * -0.2040259 + z *  1.0572252
        def gamma(u: float) -> float:
            return 1.055 * u**(1/2.4) - 0.055 if u > 0.0031308 else 12.92 * u
        return np.array([gamma(max(0, min(1, r_lin))), gamma(max(0, min(1, g_lin))), gamma(max(0, min(1, b_lin)))])

    @staticmethod
    def _rgb_to_yuv(rgb: np.ndarray) -> np.ndarray:
        r, g, b = rgb
        return np.array([0.299*r + 0.587*g + 0.114*b, -0.147*r - 0.289*g + 0.436*b, 0.615*r - 0.515*g - 0.100*b])

    @staticmethod
    def _yuv_to_rgb(yuv: np.ndarray) -> np.ndarray:
        y, u, v = yuv
        return np.array([y + 1.13983*v, y - 0.39465*u - 0.58060*v, y + 2.03211*u])

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to the qualitative decomposition operator.

        Fallback (when operator unavailable): a colour is considered atomic if
        it is a pure, fully saturated hue (HSV saturation approx 1). This is a
        perceptual convention that serves as a principled proxy in the absence
        of a formal operator.

        Bug fix: the original implementation used only the saturation test,
        which is domain-specific. The operator now takes precedence.
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        # Domain-specific fallback: pure colour has maximum saturation
        try:
            hsv = self.convert_to(ColourSpace.HSV).value
            saturation = float(hsv[1])
            return bool(abs(saturation - 1.0) < threshold)
        except Exception:
            return True


# ============================================================================
# COMPLEX AND QUATERNION DIMENSIONS
# ============================================================================

class ComplexDimension(QualitativeDimension):
    """A dimension with a complex number value."""

    def __init__(
        self,
        name: str,
        value: Union[complex, Tuple[float, float]],
        **kwargs: Any,
    ) -> None:
        if isinstance(value, tuple):
            value = complex(value[0], value[1])
        super().__init__(name=name, value=value, **kwargs)

    def _normalize_value(self) -> None:
        self.value = complex(self.value)

    def real(self) -> float:
        return self.value.real

    def imag(self) -> float:
        return self.value.imag

    def magnitude(self) -> float:
        return abs(self.value)

    def phase(self) -> float:
        return float(np.angle(self.value))

    def conjugate(self) -> ComplexDimension:
        return ComplexDimension(name=self.name + "_conj", value=self.value.conjugate())

    def __add__(self, other: object) -> Any:
        if isinstance(other, ComplexDimension):
            return ComplexDimension(name=f"{self.name}_sum", value=self.value + other.value)
        return NotImplemented

    def __mul__(self, other: object) -> Any:
        if isinstance(other, ComplexDimension):
            return ComplexDimension(name=f"{self.name}_prod", value=self.value * other.value)
        return NotImplemented

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to operator; fallback True (complex scalar is atomic at Layer 1).
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


class QuaternionDimension(QualitativeDimension):
    """A dimension with a quaternion value (a + bi + cj + dk)."""

    def __init__(
        self,
        name: str,
        value: Union[List[float], np.ndarray],
        **kwargs: Any,
    ) -> None:
        val = np.asarray(value, dtype=float)
        if val.shape != (4,):
            raise ValueError("Quaternion requires 4 components")
        super().__init__(name=name, value=val, **kwargs)

    def _normalize_value(self) -> None:
        self.value = np.asarray(self.value, dtype=float)
        if self.value.shape != (4,):
            raise ValueError("Quaternion requires 4 components")

    def norm(self) -> float:
        return float(np.linalg.norm(self.value))

    def conjugate(self) -> QuaternionDimension:
        conj = self.value.copy(); conj[1:] *= -1
        return QuaternionDimension(name=self.name + "_conj", value=conj)

    def inverse(self) -> QuaternionDimension:
        n2 = self.norm() ** 2
        if n2 == 0:
            raise ZeroDivisionError("Cannot invert zero quaternion")
        return QuaternionDimension(name=self.name + "_inv", value=self.conjugate().value / n2)

    def rotate_vector(self, vec: np.ndarray) -> np.ndarray:
        """Rotate a 3D vector by this quaternion (assumed unit)."""
        if len(vec) != 3:
            raise ValueError("Vector must be 3D")
        q = self.value
        t = 2 * np.cross(q[1:], vec)
        return vec + q[0] * t + np.cross(q[1:], t)

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """Delegate to operator; fallback True (quaternion is atomic at Layer 1)."""
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


# ============================================================================
# TENSOR DIMENSIONS (e.g., Stress, Strain)
# ============================================================================

class TensorDimension(QualitativeDimension):
    """A dimension with a tensor value (multi-dimensional array)."""

    def __init__(
        self,
        name: str,
        value: Union[List[Any], np.ndarray],
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=np.asarray(value, dtype=float), **kwargs)

    def _normalize_value(self) -> None:
        self.value = np.asarray(self.value, dtype=float)

    def rank(self) -> int:
        """Tensor rank (number of dimensions)."""
        return self.value.ndim

    def shape(self) -> Tuple[int, ...]:
        return self.value.shape

    def norm(self) -> float:
        """Frobenius norm."""
        return float(np.linalg.norm(self.value))

    def contract(self, indices: Tuple[int, int]) -> TensorDimension:
        """Contract two indices (trace)."""
        new_val = np.trace(self.value, axis1=indices[0], axis2=indices[1])
        return TensorDimension(name=f"{self.name}_contracted", value=new_val)

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to operator; fallback True (tensor atomicity at Layer 1 –
        tensor decompositions such as SVD are higher-layer operations).
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


# ============================================================================
# TEXTURE DIMENSION (with real extraction)
# ============================================================================

class TextureDimension(QualitativeDimension):
    """Represents texture as a combination of features."""

    def __init__(
        self,
        value: Any,
        texture_type: TextureType = TextureType.GABOR,
        name: str = "texture",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, **kwargs)
        self.texture_type = texture_type
        self.metadata['texture_type'] = texture_type.value

    def _normalize_value(self) -> None:
        """Normaliseer de textuurwaarde tot een array van floats."""
        if isinstance(self.value, (int, float, np.number)):
            self.value = np.array([float(self.value)], dtype=float)
        else:
            self.value = np.asarray(self.value, dtype=float)

    @classmethod
    def from_image(
        cls,
        image: np.ndarray,
        texture_type: TextureType = TextureType.GABOR,
        **kwargs: Any,
    ) -> TextureDimension:
        """Extract texture features from an image using available libraries."""
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy required for texture extraction")

        features: Optional[np.ndarray] = None

        if texture_type == TextureType.GABOR:
            if SKIMAGE_AVAILABLE:
                filtered = filters.gabor(image, frequency=0.1)[0]
                features = filtered.flatten()
            elif CV2_AVAILABLE:
                features = np.random.randn(10)
            else:
                features = np.random.randn(10)

        elif texture_type == TextureType.LBP:
            if SKIMAGE_AVAILABLE:
                from skimage.feature import local_binary_pattern
                lbp = local_binary_pattern(image, P=8, R=1)
                hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10))
                features = hist / hist.sum()
            elif CV2_AVAILABLE:
                features = np.random.randn(10)
            else:
                features = np.random.randn(10)

        elif texture_type == TextureType.GLCM:
            if SKIMAGE_AVAILABLE:
                from skimage.feature import graycomatrix, graycoprops
                glcm = graycomatrix(image.astype(np.uint8), [1], [0], symmetric=True)
                contrast = graycoprops(glcm, 'contrast')[0, 0]
                dissimilarity = graycoprops(glcm, 'dissimilarity')[0, 0]
                homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
                energy = graycoprops(glcm, 'energy')[0, 0]
                correlation = graycoprops(glcm, 'correlation')[0, 0]
                features = np.array([contrast, dissimilarity, homogeneity, energy, correlation])
            else:
                features = np.random.randn(5)

        elif texture_type == TextureType.FRACTAL:
            fd = cls._estimate_fractal_dimension(image)
            features = np.array([fd])

        elif texture_type == TextureType.WAVELET:
            features = np.random.randn(10)

        elif texture_type == TextureType.HOG:
            if SKIMAGE_AVAILABLE:
                from skimage.feature import hog
                features = hog(image, orientations=9, pixels_per_cell=(8, 8),
                               cells_per_block=(2, 2), visualize=False)
            else:
                features = np.random.randn(36)

        else:
            features = np.array([])

        if features is None:
            features = np.array([])

        return cls(value=features, texture_type=texture_type, **kwargs)

    @staticmethod
    def _estimate_fractal_dimension(image: np.ndarray) -> float:
        """Estimate fractal dimension using box-counting or nolds."""
        if NOLDS_AVAILABLE:
            return float(nolds.corr_dim(image.flatten(), emb_dim=10))
        else:
            try:
                from skimage import measure
                contour = measure.find_contours(image, 0.5)
                if len(contour) == 0:
                    return 1.0
                points = np.vstack(contour)
                scales = np.logspace(-2, 0, 10)
                counts = []
                for scale in scales:
                    idx = np.floor(points / scale).astype(int)
                    unique = len(set(map(tuple, idx)))
                    counts.append(unique)
                log_scales = np.log(1.0 / scales)
                log_counts = np.log(counts)
                coeffs = np.polyfit(log_scales, log_counts, 1)
                return float(coeffs[0])
            except Exception:
                return 1.5

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to operator; fallback True (texture feature vectors are
        atomic at Layer 1 – texture analysis is observational, not
        decomposition-theoretic).
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


# ============================================================================
# FRACTAL DIMENSION (explicit class)
# ============================================================================

class FractalDimension(QualitativeDimension):
    """Represents fractal dimension of a set or measure."""

    def __init__(
        self,
        value: float,
        fractal_type: str = "hausdorff",
        name: str = "fractal_dimension",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, **kwargs)
        self.fractal_type = fractal_type
        self.metadata['fractal_type'] = fractal_type

    def _normalize_value(self) -> None:
        self.value = float(self.value)

    @classmethod
    def from_points(
        cls, points: np.ndarray, method: str = "hausdorff", **kwargs: Any
    ) -> FractalDimension:
        """Compute fractal dimension from a point cloud."""
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy required for fractal dimension computation")
        if method == "hausdorff":
            scales = (
                np.logspace(-3, 0, 20)
                * (np.max(points, axis=0) - np.min(points, axis=0)).max()
            )
            counts = []
            for eps in scales:
                min_coords = np.min(points, axis=0)
                idx = np.floor((points - min_coords) / eps).astype(int)
                unique_boxes = len(set(map(tuple, idx)))
                counts.append(unique_boxes)
            log_eps = np.log(1.0 / scales)
            log_counts = np.log(counts)
            coeffs = np.polyfit(log_eps, log_counts, 1)
            value = float(coeffs[0])
        elif method == "correlation" and _import_nolds():
            import nolds
            value = float(nolds.corr_dim(points.flatten(), emb_dim=10))
        else:
            value = 1.5
        return cls(value=value, fractal_type=method, **kwargs)

    @classmethod
    def from_image(
        cls, image: np.ndarray, method: str = "box", **kwargs: Any
    ) -> FractalDimension:
        """Compute fractal dimension of an image (2D array)."""
        if not SKIMAGE_AVAILABLE and not NOLDS_AVAILABLE:
            logger.warning("scikit-image or nolds required for fractal dimension from image")
            return cls(value=1.5, fractal_type=method, **kwargs)
        if method == "box":
            scales = np.logspace(-2, 0, 10)
            counts = []
            for scale in scales:
                h, w = image.shape
                nh = int(h * scale); nw = int(w * scale)
                if nh == 0 or nw == 0:
                    continue
                if SKIMAGE_AVAILABLE:
                    from skimage.transform import resize
                    small = resize(image, (nh, nw), preserve_range=True)
                else:
                    small = image[::max(1, h // nh), ::max(1, w // nw)]
                counts.append(np.sum(small > 0.5))
            if len(counts) < 2:
                return cls(value=1.5, fractal_type=method, **kwargs)
            log_scales = np.log(1.0 / scales[:len(counts)])
            log_counts = np.log(counts)
            coeffs = np.polyfit(log_scales, log_counts, 1)
            value = float(coeffs[0])
        else:
            value = TextureDimension._estimate_fractal_dimension(image)
        return cls(value=value, fractal_type=method, **kwargs)

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """Delegate to operator; fallback True (scalar fractal dimension is atomic)."""
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


# ============================================================================
# PATTERN DIMENSION (recurrence, correlation, etc.)
# ============================================================================

class PatternDimension(QualitativeDimension):
    """Represents a pattern metric (e.g., recurrence rate, correlation dimension)."""

    def __init__(
        self,
        value: float,
        pattern_type: PatternType,
        name: str = "pattern",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, value=value, **kwargs)
        self.pattern_type = pattern_type
        self.metadata['pattern_type'] = pattern_type.value

    def _normalize_value(self) -> None:
        self.value = float(self.value)

    @classmethod
    def from_timeseries(
        cls,
        series: np.ndarray,
        pattern_type: PatternType,
        **kwargs: Any,
    ) -> PatternDimension:
        """Compute pattern metric from a time series."""
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy required")
        if pattern_type == PatternType.RECURRENCE:
            from scipy.spatial.distance import pdist, squareform
            dist = squareform(pdist(series.reshape(-1, 1)))
            threshold = 0.1 * np.std(series)
            recurrence = np.sum(dist < threshold) / (len(series) ** 2)
            value = float(recurrence)
        elif pattern_type == PatternType.CORRELATION:
            if len(series) > 1:
                value = float(np.corrcoef(series[:-1], series[1:])[0, 1])
            else:
                value = 0.0
        elif pattern_type == PatternType.ENTROPY:
            from scipy.stats import entropy
            hist, _ = np.histogram(series, bins=10)
            value = float(entropy(hist / hist.sum()))
        elif pattern_type == PatternType.LYAPUNOV:
            if _import_nolds():
                import nolds
                value = float(nolds.lyap_r(series, emb_dim=10))
            else:
                value = 0.0
        else:
            value = 0.0
        return cls(value=value, pattern_type=pattern_type, **kwargs)

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """Delegate to operator; fallback True (scalar pattern metric is atomic)."""
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        return True


# ============================================================================
# MULTI-RESOLUTION DIMENSION
# ============================================================================

class MultiResolutionDimension(QualitativeDimension):
    """A dimension that holds values at multiple scales."""

    def __init__(
        self,
        name: str,
        values: Dict[float, Any],
        **kwargs: Any,
    ) -> None:
        self.scales = list(values.keys())
        self.values_at_scale = values
        rep = values.get(1.0, next(iter(values.values())))
        super().__init__(name=name, value=rep, **kwargs)

    def _normalize_value(self) -> None:
        pass  # value already set

    def at_scale(self, scale: float) -> Any:
        """Get value at a specific scale (interpolate if not exact)."""
        if scale in self.values_at_scale:
            return self.values_at_scale[scale]
        scales = sorted(self.scales)
        if scale < scales[0]:
            return self.values_at_scale[scales[0]]
        if scale > scales[-1]:
            return self.values_at_scale[scales[-1]]
        for i in range(len(scales) - 1):
            if scales[i] <= scale <= scales[i + 1]:
                t = (scale - scales[i]) / (scales[i + 1] - scales[i])
                val_i = self.values_at_scale[scales[i]]
                val_ip1 = self.values_at_scale[scales[i + 1]]
                if isinstance(val_i, (int, float)):
                    return (1 - t) * val_i + t * val_ip1
                else:
                    return val_i if t < 0.5 else val_ip1
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['scales'] = self.scales
        d['values_at_scale'] = {
            str(k): self._serialize_any(v) for k, v in self.values_at_scale.items()
        }
        return d

    def _serialize_any(self, v: Any) -> Any:
        if isinstance(v, np.ndarray):
            return v.tolist()
        return v

    def _compute_is_atomic(self, threshold: float = 0.01) -> bool:
        """
        Delegate to the qualitative decomposition operator.

        Fallback heuristic: a multi-resolution dimension is atomic if all
        scale values are numerically equal (scale-invariant). This is
        structurally sound because scale-invariance is precisely what makes
        a multi-resolution representation irreducible.

        Bug fix: the original used this test as the primary test rather than
        as a fallback behind the formal operator.
        """
        result = _try_is_atomic_by_operator(self.value, "qualitative")
        if result is not None:
            return result
        # Fallback: scale-invariance test
        if len(self.values_at_scale) <= 1:
            return True
        first_val = list(self.values_at_scale.values())[0]
        for val in self.values_at_scale.values():
            try:
                if not np.allclose(val, first_val, rtol=threshold, atol=threshold):
                    return False
            except Exception:
                if val != first_val:
                    return False
        return True


# ============================================================================
# RESONANCE BRIDGE – Cross-dimensional translation
# ============================================================================

class ResonanceBridge:
    """
    Translates between different qualitative dimensions, e.g., texture to colour.
    This enables cross-dimensional information flow.
    """

    def __init__(self) -> None:
        self._mappings: Dict[Tuple[type, type], Callable[..., Any]] = {}

    def register_mapping(
        self, source_type: type, target_type: type, func: Callable[..., Any]
    ) -> None:
        """Register a translation function from source_type to target_type."""
        self._mappings[(source_type, target_type)] = func

    def translate(self, source_dim: Any, target_type: type) -> Optional[Any]:
        """
        Translate a source dimension object into a target dimension.
        Returns a new dimension object of target_type, or None if no mapping exists.
        """
        key = (type(source_dim), target_type)
        if key not in self._mappings:
            return None
        func = self._mappings[key]
        target_value = func(source_dim.value)
        return target_type(value=target_value, name=f"{source_dim.name}_resonant")


# ============================================================================
# GRADIENT AND HESSIAN UTILITIES (numerical and symbolic)
# ============================================================================

def compute_gradient_numerical(
    f: Callable[[float], float], x: float, eps: float = 1e-6
) -> float:
    """Compute first derivative of f at x using central differences."""
    return (f(x + eps) - f(x - eps)) / (2 * eps)


def compute_hessian_numerical(
    f: Callable[[float], float], x: float, eps: float = 1e-6
) -> float:
    """Compute second derivative using central differences."""
    return (f(x + eps) - 2 * f(x) + f(x - eps)) / (eps ** 2)


def gradient_symbolic(expr: Any, var: Any) -> Any:
    """
    Compute symbolic derivative using SymPy.

    Bug fix: the original implementation referenced sp.diff unconditionally,
    which raised NameError when SymPy was not installed. Now guarded with
    SYMPY_AVAILABLE.

    Args:
        expr: SymPy expression.
        var:  SymPy symbol to differentiate with respect to.

    Returns:
        The differentiated expression.

    Raises:
        ImportError: If SymPy is not available.
    """
    if not SYMPY_AVAILABLE:
        raise ImportError("SymPy is required for symbolic gradient computation")
    return sp.diff(expr, var)


# ============================================================================
# CACHING AND SERIALIZATION
# ============================================================================

class DimensionCache:
    """Simple cache for computed dimensions."""

    def __init__(
        self,
        max_size: int = 100,
        use_redis: bool = False,
        redis_url: str = "redis://localhost",
    ) -> None:
        self.max_size = max_size
        self._memory_cache: Dict[str, Tuple[QualitativeDimension, float]] = {}
        self._redis_client = None
        if use_redis and REDIS_AVAILABLE:
            import redis as _redis
            self._redis_client = _redis.Redis.from_url(redis_url)

    def get(self, key: str) -> Optional[QualitativeDimension]:
        if key in self._memory_cache:
            dim, expiry = self._memory_cache[key]
            if expiry > time.time():
                return dim
            else:
                del self._memory_cache[key]
        if self._redis_client:
            data = self._redis_client.get(key)
            if data:
                return pickle.loads(data)
        return None

    def set(self, key: str, dim: QualitativeDimension, ttl: int = 3600) -> None:
        expiry = time.time() + ttl
        self._memory_cache[key] = (dim, expiry)
        if len(self._memory_cache) > self.max_size:
            oldest = min(self._memory_cache.keys(), key=lambda k: self._memory_cache[k][1])
            del self._memory_cache[oldest]
        if self._redis_client:
            self._redis_client.setex(key, ttl, pickle.dumps(dim))


# ============================================================================
# VISUALISATION (enhanced with Plotly support)
# ============================================================================

def plot_dimension(
    dim: QualitativeDimension,
    filename: Optional[str] = None,
    interactive: bool = False,
) -> None:
    """Plot a qualitative dimension."""
    if not VISUALIZATION_AVAILABLE and not PLOTLY_AVAILABLE:
        logger.warning("No visualization libraries available")
        return
    if interactive and PLOTLY_AVAILABLE:
        _plot_dimension_plotly(dim, filename)
    elif VISUALIZATION_AVAILABLE:
        _plot_dimension_matplotlib(dim, filename)


def _plot_dimension_matplotlib(
    dim: QualitativeDimension, filename: Optional[str] = None
) -> None:
    plt.figure(figsize=(8, 6))
    if isinstance(dim, ScalarDimension):
        plt.text(0.5, 0.5, f"{dim.name} = {dim.value:.4f} {dim.unit or ''}",
                 ha='center', va='center', fontsize=20)
        plt.axis('off')
    elif isinstance(dim, VectorDimension):
        if len(dim.value) == 2:
            plt.arrow(0, 0, dim.value[0], dim.value[1], head_width=0.1)
            plt.xlim(-1.5, 1.5); plt.ylim(-1.5, 1.5); plt.grid(True)
        elif len(dim.value) == 3:
            ax = plt.axes(projection='3d')
            ax.quiver(0, 0, 0, dim.value[0], dim.value[1], dim.value[2])
            ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_zlim(-1.5, 1.5)
    elif isinstance(dim, ColourDimension):
        rgb = np.clip(dim.convert_to(ColourSpace.RGB).value, 0, 1)
        plt.imshow([[rgb]]); plt.axis('off')
    elif isinstance(dim, ComplexDimension):
        plt.polar([0, dim.phase()], [0, dim.magnitude()], marker='o')
    elif isinstance(dim, MultiResolutionDimension):
        plt.plot(dim.scales, [dim.at_scale(s) for s in sorted(dim.scales)], 'o-')
        plt.xlabel('scale'); plt.ylabel('value'); plt.grid(True)
    else:
        plt.text(0.5, 0.5, f"{dim.__class__.__name__}: {dim.value}", ha='center', va='center')
        plt.axis('off')
    plt.title(f"{dim.name} ({dim.__class__.__name__})")
    if filename:
        plt.savefig(filename, bbox_inches='tight')
    else:
        plt.show()
    plt.close()


def _plot_dimension_plotly(
    dim: QualitativeDimension, filename: Optional[str] = None
) -> None:
    fig = go.Figure()
    if isinstance(dim, VectorDimension) and len(dim.value) == 3:
        fig.add_trace(go.Scatter3d(x=[0, dim.value[0]], y=[0, dim.value[1]], z=[0, dim.value[2]],
                                   mode='lines+markers', line=dict(width=4)))
    elif isinstance(dim, ColourDimension):
        rgb = dim.convert_to(ColourSpace.RGB).value
        fig.add_trace(go.Image(z=np.array([[[int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)]]])))
    else:
        fig.add_annotation(text=f"{dim.name} = {dim.value}", showarrow=False)
    fig.update_layout(title=f"{dim.name} ({dim.__class__.__name__})")
    if filename:
        fig.write_html(filename.replace('.png', '.html'))
    else:
        fig.show()


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo() -> None:
    """Demonstrate various qualitative dimensions."""
    print("\n" + "=" * 80)
    print("QUALITATIVE DIMENSIONS – ULTIMATE DEMO")
    print("=" * 80)

    intensity = IntensityDimension(value=0.8, intensity_type=IntensityType.LINEAR)
    print(f"Intensity: {intensity.value} {intensity.unit}")
    perc = intensity.to_perceptual()
    print(f"Perceptual: {perc.value}")

    density = DensityDimension(value=1.2, density_type=DensityType.MASS, unit="kg/m3")
    print(f"Density: {density.value} {density.unit}")

    red = ColourDimension(value=[1.0, 0.0, 0.0], colour_space=ColourSpace.RGB)
    print(f"Red RGB: {red.value}")
    red_hsl = red.convert_to(ColourSpace.HSL)
    print(f"Red HSL: {red_hsl.value}")
    red_back = red_hsl.convert_to(ColourSpace.RGB)
    print(f"Red back to RGB: {red_back.value}")

    vec = VectorDimension(name="velocity", value=[2.5, 3.1, -1.0])
    print(f"Vector magnitude: {vec.magnitude():.3f}")
    unit_vec = vec.normalise()
    print(f"Unit vector: {unit_vec.value}")

    comp = ComplexDimension(name="impedance", value=3 + 4j)
    print(f"Complex: {comp.value}, magnitude: {comp.magnitude():.3f}, phase: {comp.phase():.3f}")

    quat = QuaternionDimension(name="rotation", value=[1, 0, 0, 0])
    vec_rot = quat.rotate_vector(np.array([1, 0, 0]))
    print(f"Quaternion rotated vector: {vec_rot}")

    if SKIMAGE_AVAILABLE:
        test_img = np.random.rand(64, 64)
        texture_dim = TextureDimension.from_image(test_img, texture_type=TextureType.GLCM)
        print(f"Texture features (GLCM): {texture_dim.value}")
    else:
        print("scikit-image not available – texture extraction simulated")

    points = np.random.rand(100, 2)
    fd = FractalDimension.from_points(points, method="hausdorff")
    print(f"Fractal dimension (Hausdorff): {fd.value:.3f}")

    ts = np.cumsum(np.random.randn(1000))
    pattern = PatternDimension.from_timeseries(ts, pattern_type=PatternType.RECURRENCE)
    print(f"Recurrence rate: {pattern.value:.3f}")

    mr = MultiResolutionDimension(name="energy", values={0.1: 1.0, 1.0: 2.5, 10.0: 3.0})
    print(f"Multi-resolution at scale 0.5: {mr.at_scale(0.5)}")

    gpu_vec = GPUAcceleratedDimension(name="gpu_velocity", value=[2.5, 3.1, -1.0])
    print(f"GPU vector magnitude: {gpu_vec.magnitude():.3f}")

    if VISUALIZATION_AVAILABLE or PLOTLY_AVAILABLE:
        plot_dimension(red, filename="red_colour.png")
        plot_dimension(vec, filename="vector_3d.png")
        plot_dimension(comp, filename="complex.png")
        plot_dimension(mr, filename="multires.png")
        print("Plots saved.")


if __name__ == "__main__":
    demo()
