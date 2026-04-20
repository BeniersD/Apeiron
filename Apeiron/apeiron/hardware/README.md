## 🖥️ Hardware Abstraction Layer

APEIRON includes a hardware abstraction layer that automatically selects
the best available backend for your system.

### Supported backends

| Backend | Description | Requirements |
| :--- | :--- | :--- |
| `cpu` | NumPy‑based CPU backend (always available) | NumPy |
| `cuda` | GPU acceleration via PyTorch | PyTorch, CUDA |
| `fpga` | Xilinx FPGA acceleration via PYNQ | PYNQ, compatible board |
| `quantum` | Quantum simulator / real hardware via Qiskit | Qiskit |

### Usage

```python
from apeiron.hardware import get_best_backend

backend = get_best_backend()
field = backend.create_continuous_field(1024)