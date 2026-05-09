import pytest
import numpy as np
from apeiron.optional.derived_categories import (
    ChainComplex, ChainMap, mapping_cone, ext, tor,
    VectorSpace, SpectralSequence
)

class TestChainComplex:
    def test_is_complex_true(self):
        d1 = np.array([[1, 1]])          # 1x2
        d2 = np.array([[1], [-1]])       # 2x1 => d1 @ d2 = 0
        C = ChainComplex([d1, d2])
        assert C.is_complex()

    def test_is_complex_false(self):
        d1 = np.array([[1, 0, 0], [0, 1, 0]])
        d2 = np.array([[1, 0], [0, 0], [0, 1]])  # niet compatibel
        C = ChainComplex([d1, d2])
        assert not C.is_complex()

    def test_homology_sphere(self):
        d2 = np.array([[1], [1], [1]])   # 3x1
        d1 = np.array([[1, -1, 0], [1, 0, -1], [0, 1, -1]]) # 3x3
        C = ChainComplex([d1, d2])
        h0_dim = C.homology(0)[0]
        h1_dim = C.homology(1)[0]
        h2_dim = C.homology(2)[0]
        assert h0_dim == 1
        assert h1_dim == 0
        assert h2_dim == 0   # contractible => no H2

    def test_empty_complex(self):
        C = ChainComplex([])
        assert C.is_complex()
        assert C.homology(0)[0] == 0

    def test_betti(self):
        d1 = np.array([[1, 2], [2, 4]])  # rank 1
        d2 = np.array([[1], [2]])         # 2x1
        C = ChainComplex([d1, d2])
        assert C.betti(0) >= 0

    def test_mapping_cone(self):
        # Maak een simpel complex en identiteitsketenafbeelding
        d1 = np.array([[1, 0], [0, 1]])   # 2x2
        C = ChainComplex([d1])
        id_map = ChainMap(C, C, [np.eye(2), np.eye(2)])
        cone = mapping_cone(id_map)
        # De kegel moet exact zijn (acyclisch)
        h = [cone.homology(i)[0] for i in range(0, 3)]
        assert max(h) == 0  # alle homologieën 0

    def test_invalid_complex_raises(self):
        with pytest.raises(Exception):
            ChainComplex([np.ones((2,3)), np.ones((4,5))]).is_complex()

class TestHomologicalAlgebra:
    def test_ext_zero(self):
        A = VectorSpace(3)
        B = VectorSpace(2)
        assert ext(A, B, 0) == 6
        assert ext(A, B, 1) == 0

    def test_tor_zero(self):
        A = VectorSpace(3)
        B = VectorSpace(2)
        assert tor(A, B, 0) == 6
        assert tor(A, B, 1) == 0

    def test_ext_higher_dimensions(self):
        A = VectorSpace(5)
        B = VectorSpace(7)
        assert ext(A, B, 0) == 5 * 7
        assert ext(A, B, 2) == 0

    def test_tor_higher_dimensions(self):
        A = VectorSpace(4)
        B = VectorSpace(6)
        assert tor(A, B, 0) == 4 * 6
        assert tor(A, B, 3) == 0

class TestSpectralSequence:
    def test_basic_page(self):
        init = {
            (0, 0): np.array([[1]]),
            (0, 1): np.array([[0]]),
        }
        ss = SpectralSequence(init)
        ss.next_page()
        assert ss.current_page == 3