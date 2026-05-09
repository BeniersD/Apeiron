import numpy as np
from apeiron.optional.quantum_error_correction import (
    RepetitionCode, ShorCode, SteaneCode, FiveQubitCode,
    LookupTableDecoder
)

class TestRepetitionCode:
    # Oorspronkelijke tests blijven
    def code(self):
        return RepetitionCode(n=3)

    def test_encoding_circuit(self):
        code = self.code()
        circ = code.encode_circuit()
        assert circ.num_qubits == 3

    def test_syndrome_for_bitflip(self):
        code = self.code()
        error = ['X', 'I', 'I']          # X op qubit 0
        synd = code.compute_syndrome(error)
        assert synd == [1, 0]   # Z1Z2 en Z2Z3

    def test_decode_corrects_error(self):
        code = self.code()
        decoder = LookupTableDecoder(code)
        error = ['I', 'X', 'I']          # X op qubit 1
        synd = code.compute_syndrome(error)
        correction = decoder.decode(synd)
        assert correction == {1: 'X'}

class TestShorCode:
    def code(self):
        return ShorCode()

    def test_encoding_circuit_qubits(self):
        circ = self.code().encode_circuit()
        assert circ.num_qubits == 9

    def test_syndrome_for_X0(self):
        code = self.code()
        decoder = LookupTableDecoder(code)
        error = ['X'] + ['I']*8
        synd = code.compute_syndrome(error)
        correction = decoder.decode(synd)
        assert correction.get(0, 'I') == 'X'

class TestSteaneCode:
    def code(self):
        return SteaneCode()

    def test_encoding_circuit_qubits(self):
        circ = self.code().encode_circuit()
        assert circ.num_qubits == 7

    def test_syndrome_for_X3(self):
        code = self.code()
        decoder = LookupTableDecoder(code)
        error = ['I']*3 + ['X'] + ['I']*3
        synd = code.compute_syndrome(error)
        correction = decoder.decode(synd)
        assert correction.get(3, 'I') == 'X'

class TestFiveQubitCode:
    def code(self):
        return FiveQubitCode()

    def test_encoding_circuit_qubits(self):
        circ = self.code().encode_circuit()
        assert circ.num_qubits == 5

    def test_syndrome_for_Z2(self):
        code = self.code()
        decoder = LookupTableDecoder(code)
        error = ['I']*2 + ['Z'] + ['I']*2
        synd = code.compute_syndrome(error)
        correction = decoder.decode(synd)
        assert correction.get(2, 'I') == 'Z'

    def test_unique_syndromes(self):
        """Alle enkelvoudige fouten moeten een uniek syndroom hebben (code is perfect)."""
        code = self.code()
        stabilizers = code.stabilizers()
        syndromes = set()
        for qubit in range(5):
            for pauli in ['X', 'Y', 'Z']:
                error = ['I']*5
                error[qubit] = pauli
                synd = tuple(code.compute_syndrome(error))
                syndromes.add(synd)
        # 5 qubits * 3 Paulis = 15 unieke syndromen
        assert len(syndromes) == 15