"""
BACKENDS PACKAGE - Hardware backend implementaties
================================================================================
Bevat alle hardware backend implementaties:
- CPU backend (numpy) – met O(1) lookups
- CUDA/GPU backend (torch)
- FPGA backend (PYNQ) – met fixed-point conversie
- Quantum backend (Qiskit) – met gecorrigeerde SWAP-test

Dit package maakt het mogelijk om hardware backends te importeren via:
    from apeiron.hardware.backends import CPUBackend, CUDABackend
"""

from .backend import HardwareBackend
from .cpu_backend import CPUBackend
from .cuda_backend import CUDABackend
from .fpga_backend import FPGABackend
from .quantum_backend import QuantumBackend

__all__ = [
    'HardwareBackend',
    'CPUBackend',
    'CUDABackend',
    'FPGABackend',
    'QuantumBackend',
]