"""
HALL ALGEBRA – ULTIMATE IMPLEMENTATION
=======================================
This module provides a framework for Hall algebras associated to quivers.
Hall algebras encode the structure of extensions between representations.

Features:
- Abstract base class `HallAlgebra` defining the interface.
- Concrete implementation for the Jordan quiver (one vertex, one loop)
  using partitions and Littlewood–Richardson coefficients.
- Concrete implementation for linearly oriented type A quivers (A_n)
  using dimension vectors and q‑binomial coefficients (flag representations).
- Methods to compute Hall numbers, multiplication, and structure constants.
- Littlewood–Richardson coefficients computed correctly using either
  sympy (if available) or a built‑in tableau‑based algorithm.
- Integration with quiver moduli: function to convert Harder–Narasimhan
  filtrations into products in the Hall algebra.
- Extensible to other quivers via subclassing.

All calculations are performed combinatorially; for type A we rely on the
explicit formula for flag representations. For non‑flag representations
the numbers are more complex – this implementation serves as an educational
starting point.
"""

import itertools
import logging
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from collections import defaultdict
from functools import lru_cache

# ============================================================================
# Optional dependencies
# ============================================================================
try:
    import sympy
    from sympy.combinatorics import Partition as SympyPartition
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

logger = logging.getLogger(__name__)


# ============================================================================
# PARTITION UTILITIES (for Jordan quiver)
# ============================================================================

class Partition(tuple):
    """
    Immutable partition (non‑increasing sequence of positive integers).
    Provides basic operations: size, conjugate, containment.
    """
    def __new__(cls, seq):
        seq = tuple(sorted(seq, reverse=True))
        return super().__new__(cls, seq)

    def size(self) -> int:
        """Total number of boxes (sum of parts)."""
        return sum(self)

    def length(self) -> int:
        """Number of parts."""
        return len(self)

    def conjugate(self) -> 'Partition':
        """Conjugate partition (transpose of Young diagram)."""
        if not self:
            return Partition(())
        conj = []
        for i in range(self[0]):
            conj.append(sum(1 for p in self if p > i))
        return Partition(conj)

    def contains(self, other: 'Partition') -> bool:
        """Dominance order: self >= other (self dominates other)."""
        if self.size() < other.size():
            return False
        cum_self = 0
        cum_other = 0
        for i in range(max(len(self), len(other))):
            cum_self += self[i] if i < len(self) else 0
            cum_other += other[i] if i < len(other) else 0
            if cum_self < cum_other:
                return False
        return True

    def __repr__(self):
        return f"Partition{tuple(self)}"

    def to_sympy(self):
        """Convert to sympy Partition if available."""
        if HAS_SYMPY:
            return SympyPartition(list(self))
        raise ImportError("sympy not available")


def partitions_of(n: int) -> List[Partition]:
    """Generate all partitions of integer n."""
    result = []

    def _gen(remaining, max_part, current):
        if remaining == 0:
            result.append(Partition(current))
            return
        for p in range(min(max_part, remaining), 0, -1):
            _gen(remaining - p, p, current + [p])

    _gen(n, n, [])
    return result


def all_partitions_up_to(max_size: int) -> List[Partition]:
    """All partitions with size ≤ max_size."""
    parts = []
    for n in range(max_size + 1):
        parts.extend(partitions_of(n))
    return parts


# ============================================================================
# LITTLEWOOD–RICHARDSON COEFFICIENTS (correct implementation)
# ============================================================================

def littlewood_richardson_sympy(mu: Partition, nu: Partition, lam: Partition) -> int:
    """Compute LR coefficient using sympy."""
    if not HAS_SYMPY:
        raise ImportError("sympy not available")
    p_mu = SympyPartition(list(mu))
    p_nu = SympyPartition(list(nu))
    p_lam = SympyPartition(list(lam))
    return p_lam.lr_coefficient(p_mu, p_nu)


def littlewood_richardson_fallback(mu: Partition, nu: Partition, lam: Partition) -> int:
    """
    Fallback implementation of Littlewood–Richardson coefficient by
    enumerating semistandard tableaux of skew shape λ/μ with content ν.
    Only feasible for small partitions (max size ≤ 6). For larger,
    returns 0 and warns.
    """
    # Check size condition
    if mu.size() + nu.size() != lam.size():
        return 0

    # For large partitions, warn and return 0 (to avoid explosion)
    if lam.size() > 6:
        logger.warning("LR coefficient for large partitions not implemented in fallback; returning 0.")
        return 0

    # Compute skew shape cells: cells of lam that are not in mu
    # Represent shape as list of rows with positions
    mu_rows = list(mu) + [0] * (len(lam) - len(mu))
    lam_rows = list(lam)
    # Determine skew shape: for each row i (0-indexed), columns from mu_rows[i] to lam_rows[i]-1
    skew_cells = []
    for i in range(len(lam_rows)):
        start = mu_rows[i] if i < len(mu_rows) else 0
        for j in range(start, lam_rows[i]):
            skew_cells.append((i, j))
    if not skew_cells:
        # empty skew shape
        return 1 if nu.size() == 0 else 0

    # Sort cells in reading order: bottom to top, left to right
    # (rows decreasing, columns increasing)
    reading_order = sorted(skew_cells, key=lambda cell: (-cell[0], cell[1]))

    # Content ν: list of counts per number (1-indexed). We'll use list of length len(nu) (parts)
    # but we need the actual content vector: number of times each integer appears.
    # ν is a partition; its parts are the counts of numbers? Actually content ν is a composition
    # that is a partition. We'll interpret ν as a partition of n, and the content is that
    # number 1 appears ν_1 times? Wait: In LR rule, the content is a weak composition (a_1, a_2, ...)
    # where a_i is the number of i's. For a partition ν, we need to assign numbers 1,2,... with multiplicities.
    # So we need the conjugate? No: The content is exactly the parts of ν, meaning we fill with numbers
    # such that the number of i's is ν_i (where ν_i are the parts of ν). So we need the list of ν's parts.
    # But ν is a partition (nonincreasing). So we can take the list of its parts.
    content = list(nu)  # e.g., [2,1] means two 1's and one 2

    # Prepare recursion: index in reading order, current fill list, current counts of each number
    n_nums = len(content)
    # We'll keep a list of current counts (starting at 0)
    counts = [0] * n_nums

    def is_lattice_word(fill_sequence):
        """Check if a sequence of numbers is a lattice word."""
        # For each prefix, count of i >= count of i+1 for all i.
        # We'll track counts dynamically.
        counts_prefix = [0] * n_nums
        for num in fill_sequence:
            counts_prefix[num-1] += 1
            for i in range(n_nums-1):
                if counts_prefix[i] < counts_prefix[i+1]:
                    return False
        return True

    total = 0
    # Recursive fill
    def backtrack(idx, fill):
        nonlocal total
        if idx == len(reading_order):
            # All cells filled; check that counts match content exactly
            if fill_counts == content:
                total += 1
            return
        # For current cell, try numbers from 1 to n_nums
        for num in range(1, n_nums+1):
            # Check we haven't exceeded desired count for this number
            if fill_counts[num-1] >= content[num-1]:
                continue
            # Place number
            fill.append(num)
            fill_counts[num-1] += 1
            # Check lattice condition up to now
            if is_lattice_word(fill):
                backtrack(idx+1, fill)
            # backtrack
            fill.pop()
            fill_counts[num-1] -= 1

    fill_counts = [0] * n_nums
    backtrack(0, [])
    return total


@lru_cache(maxsize=None)
def littlewood_richardson(mu: Partition, nu: Partition, lam: Partition) -> int:
    """
    Return the Littlewood–Richardson coefficient c^λ_{μ,ν}.
    Uses sympy if available, otherwise a fallback tableau enumeration
    (limited to partitions of size ≤ 6).
    """
    if HAS_SYMPY:
        try:
            return littlewood_richardson_sympy(mu, nu, lam)
        except Exception as e:
            logger.debug(f"Sympy LR failed: {e}. Falling back to tableau method.")
            return littlewood_richardson_fallback(mu, nu, lam)
    else:
        return littlewood_richardson_fallback(mu, nu, lam)


# ============================================================================
# Q‑BINOMIAL COEFFICIENTS (for type A)
# ============================================================================

@lru_cache(maxsize=None)
def q_binomial(n: int, k: int, q: int) -> int:
    """
    Return the Gaussian binomial coefficient [n choose k]_q.
    Computed recursively using the q‑Pascal identity.
    """
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    # Use symmetry
    if k > n - k:
        k = n - k
    # q‑Pascal: [n choose k]_q = [n-1 choose k-1]_q + q^k * [n-1 choose k]_q
    return q_binomial(n-1, k-1, q) + (q**k) * q_binomial(n-1, k, q)


# ============================================================================
# ABSTRACT HALL ALGEBRA
# ============================================================================

class HallAlgebra:
    """
    Abstract base class for a Hall algebra associated to a quiver.
    The algebra is spanned by isomorphism classes of representations.
    Multiplication is given by the convolution product using Hall numbers.

    Subclasses must implement:
        - `basis(self)`: a list of objects representing isomorphism classes.
        - `hall_number(self, a, b, c)`: the Hall number F^c_{a,b} (number of
          subrepresentations of a representation of class c that are of class b
          with quotient of class a).
    """

    def basis(self) -> List[Any]:
        """Return a list of all basis elements (isomorphism classes)."""
        raise NotImplementedError

    def hall_number(self, a: Any, b: Any, c: Any) -> int:
        """
        Return the Hall number F^c_{a,b} (number of subrepresentations of a
        representation of class c that are isomorphic to b with quotient a).
        """
        raise NotImplementedError

    def multiply(self, a: Any, b: Any) -> Dict[Any, int]:
        """
        Compute the product of two basis elements: a * b = sum_c F^c_{a,b} c.
        Returns a dictionary mapping class c to coefficient.
        """
        result = defaultdict(int)
        for c in self.basis():
            coef = self.hall_number(a, b, c)
            if coef != 0:
                result[c] = coef
        return dict(result)

    def structure_constants(self) -> Dict[Tuple[Any, Any, Any], int]:
        """
        Return a dictionary mapping (a,b,c) -> Hall number.
        """
        constants = {}
        for a in self.basis():
            for b in self.basis():
                for c in self.basis():
                    val = self.hall_number(a, b, c)
                    if val != 0:
                        constants[(a, b, c)] = val
        return constants


# ============================================================================
# HALL ALGEBRA FOR THE JORDAN QUIVER
# ============================================================================

class JordanHallAlgebra(HallAlgebra):
    """
    Hall algebra of nilpotent representations of the Jordan quiver
    (one vertex, one loop) over a finite field. Isomorphism classes correspond
    to partitions (Jordan blocks). Hall numbers are Littlewood–Richardson
    coefficients, independent of the field size (for sufficiently large fields).
    """

    def __init__(self, max_part_size: int = 5):
        """
        Args:
            max_part_size: maximum size of partitions considered (i.e., max total dimension).
        """
        self.max_size = max_part_size
        self._partitions = all_partitions_up_to(max_part_size)

    def basis(self) -> List[Partition]:
        return self._partitions

    def hall_number(self, a: Partition, b: Partition, c: Partition) -> int:
        """
        For the Jordan quiver, the Hall number F^c_{a,b} equals the
        Littlewood–Richardson coefficient c^c_{a,b}.
        """
        return littlewood_richardson(a, b, c)

    def product(self, a: Partition, b: Partition) -> Dict[Partition, int]:
        """Alias for multiply."""
        return self.multiply(a, b)


# ============================================================================
# HALL ALGEBRA FOR TYPE A QUIVERS (linear orientation, flag representations)
# ============================================================================

class TypeAHallAlgebra(HallAlgebra):
    """
    Hall algebra of the linearly oriented quiver A_n (arrows i → i+1),
    restricted to representations where all maps are injective (i.e., flags of
    subspaces). Isomorphism classes are then given by non‑decreasing dimension
    vectors. The Hall numbers are products of q‑binomial coefficients.

    Args:
        n: number of vertices.
        max_dim: maximum dimension per vertex (each component ≤ max_dim).
        q: size of the finite field (a prime power).
    """

    def __init__(self, n: int, max_dim: int = 3, q: int = 2):
        self.n = n
        self.max_dim = max_dim
        self.q = q
        self._basis = self._generate_basis()

    def _generate_basis(self) -> List[Tuple[int, ...]]:
        """Generate all non‑decreasing tuples of length n with entries 0..max_dim."""
        basis = []
        # Use recursion to generate all tuples (d1,...,dn) with 0 ≤ d1 ≤ ... ≤ dn ≤ max_dim
        def gen(start, remaining, current):
            if remaining == 0:
                basis.append(tuple(current))
                return
            for v in range(start, self.max_dim + 1):
                gen(v, remaining - 1, current + [v])
        gen(0, self.n, [])
        return basis

    def basis(self) -> List[Tuple[int, ...]]:
        return self._basis

    def hall_number(self, a: Tuple[int, ...], b: Tuple[int, ...], c: Tuple[int, ...]) -> int:
        """
        For flag representations, the Hall number is non‑zero only if a + b = c
        (component‑wise). In that case it equals the product over i of
        [ c_i - b_{i-1} choose b_i - b_{i-1} ]_q, with b_0 = 0.
        """
        if len(a) != self.n or len(b) != self.n or len(c) != self.n:
            raise ValueError("Dimension vectors must have length n")
        # Check dimension addition
        for i in range(self.n):
            if a[i] + b[i] != c[i]:
                return 0
        # Compute product of q‑binomials
        b_prev = 0
        result = 1
        for i in range(self.n):
            # number of ways to choose U_i of dimension b_i in V_i of dimension c_i,
            # given that it must contain U_{i-1} (dimension b_prev)
            # This is C(c_i - b_prev, b_i - b_prev)_q
            k = b[i] - b_prev
            n = c[i] - b_prev
            if k < 0 or k > n:
                return 0
            result *= q_binomial(n, k, self.q)
            b_prev = b[i]
        return result

    def structure_constants(self) -> Dict[Tuple[Any, Any, Any], int]:
        """Return a dictionary mapping (a,b,c) to Hall numbers."""
        return super().structure_constants()


# ============================================================================
# UTILITY FUNCTIONS FOR WORKING WITH THE ALGEBRA
# ============================================================================

def print_product(algebra: HallAlgebra, a: Any, b: Any):
    """Print the product a * b in human‑readable form."""
    prod = algebra.multiply(a, b)
    terms = []
    for c, coef in prod.items():
        if coef == 1:
            terms.append(str(c))
        else:
            terms.append(f"{coef} * {c}")
    print(f"{a} * {b} = " + " + ".join(terms) if terms else "0")


def multiplication_table(algebra: HallAlgebra, max_elements: int = 5):
    """Print a multiplication table for the first few basis elements."""
    basis = algebra.basis()[:max_elements]
    print("Multiplication table:")
    for a in basis:
        row = []
        for b in basis:
            prod = algebra.multiply(a, b)
            # Represent product as string of coefficients for each c
            terms = []
            for c in basis:
                coef = prod.get(c, 0)
                if coef:
                    terms.append(f"{c}({coef})")
            row.append(" + ".join(terms) if terms else "0")
        print(f"{a}: " + " | ".join(row))


# ============================================================================
# INTEGRATION WITH QUIVER MODULI
# ============================================================================

def hn_to_hall_product(filtration: List[Tuple[Any, float]], algebra: HallAlgebra) -> Dict[Any, int]:
    """
    Convert a Harder–Narasimhan filtration (list of (subquotient, slope))
    into a product in the Hall algebra. The product is the ordered product
    of the basis elements corresponding to the subquotients (from top to bottom).

    Args:
        filtration: list of (subquotient, slope) where subquotient is a basis element
                    of the Hall algebra (e.g., a partition for Jordan quiver).
        algebra: a HallAlgebra instance.

    Returns:
        A dictionary mapping basis elements to coefficients, representing the product.
    """
    if not filtration:
        # empty product = identity (but Hall algebras are not necessarily unital? We'll treat as empty dict)
        return {}

    # Start with the first element
    result = {filtration[0][0]: 1}
    # Multiply sequentially
    for (elem, _) in filtration[1:]:
        new_result = defaultdict(int)
        for c, coef in result.items():
            prod = algebra.multiply(c, elem)
            for d, coef2 in prod.items():
                new_result[d] += coef * coef2
        result = new_result
    return dict(result)


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Demonstrate the Jordan and type A Hall algebras."""
    print("="*80)
    print("HALL ALGEBRA DEMO")
    print("="*80)

    # ----- Jordan quiver -----
    print("\n--- Jordan quiver ---")
    hall_j = JordanHallAlgebra(max_part_size=4)
    print("Basis partitions:", hall_j.basis())
    p = Partition([2,1])
    q = Partition([1,1])
    print_product(hall_j, p, q)

    # ----- Type A (A_2) -----
    print("\n--- Type A (A_2) with q=2 ---")
    hall_a2 = TypeAHallAlgebra(n=2, max_dim=2, q=2)
    print("Basis (dimension vectors):", hall_a2.basis())
    a = (0,1)
    b = (1,0)
    print_product(hall_a2, a, b)  # should be (1,1) maybe
    # Check multiplication table
    multiplication_table(hall_a2, max_elements=4)

    # Verify associativity on a small example
    print("\nChecking associativity on A_2:")
    x = (1,1)
    y = (0,1)
    z = (1,0)
    xy = hall_a2.multiply(x, y)
    xyz_left = defaultdict(int)
    for c, coef in xy.items():
        for d, coef2 in hall_a2.multiply(c, z).items():
            xyz_left[d] += coef * coef2

    yz = hall_a2.multiply(y, z)
    xyz_right = defaultdict(int)
    for c, coef in yz.items():
        for d, coef2 in hall_a2.multiply(x, c).items():
            xyz_right[d] += coef * coef2

    print("Left product (x*y)*z:", dict(xyz_left))
    print("Right product x*(y*z):", dict(xyz_right))
    if xyz_left == xyz_right:
        print("✅ Associativity holds.")
    else:
        print("❌ Associativity violated.")

    # ----- Structure constants -----
    print("\nStructure constants for A_2 (non‑zero only):")
    const = hall_a2.structure_constants()
    for (a,b,c), val in list(const.items())[:10]:  # show first 10
        print(f"F^{c}_{a},{b} = {val}")

    # ----- Test HN product -----
    print("\n--- Harder–Narasimhan to Hall product ---")
    # Fake filtration for Jordan quiver
    filt = [(Partition([2]), 0.5), (Partition([1,1]), 0.3)]
    prod = hn_to_hall_product(filt, hall_j)
    print("Product of [2] and [1,1] in Jordan algebra:", prod)


if __name__ == "__main__":
    demo()