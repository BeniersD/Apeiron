"""
QUANTUM MACHINE LEARNING – ULTIMATE IMPLEMENTATION
===================================================
This module provides quantum machine learning algorithms for use within Layer 2.
It includes:

- Quantum kernels for SVM (using PennyLane or Qiskit)
- Variational quantum classifiers (VQC) with standard and data‑reuploading circuits
- Quantum generative adversarial networks (QGAN) with quantum generator and classical discriminator
- Quantum circuit learning for regression and classification
- Data encoding functions (angle encoding, amplitude encoding)
- Integration with PennyLane, Qiskit, and PyTorch backends
- Factory function to convert Layer 1 observables to circuit inputs

All features degrade gracefully if required libraries are missing.
"""

import logging
import numpy as np
from typing import Optional, List, Tuple, Dict, Any, Callable, Union

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# PennyLane
try:
    import pennylane as qml
    from pennylane import numpy as pnp
    from pennylane.optimize import NesterovMomentum, AdamOptimizer
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False

# Qiskit
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
    from qiskit_machine_learning.algorithms import QSVC, VQC
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from qiskit.providers.aer import AerSimulator
    HAS_QISKIT_ML = True
except ImportError:
    HAS_QISKIT_ML = False

# scikit‑learn for SVM and metrics
try:
    from sklearn.svm import SVC
    from sklearn.metrics import accuracy_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# PyTorch (required for QGAN discriminator and hybrid models)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logger = logging.getLogger(__name__)


# ============================================================================
# BASE CLASS
# ============================================================================

class QuantumMLModel:
    """Base class for quantum machine learning models."""
    def __init__(self):
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit the model to data."""
        raise NotImplementedError

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict labels for X."""
        raise NotImplementedError

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return accuracy (or other metric)."""
        pred = self.predict(X)
        return np.mean(pred == y)


# ============================================================================
# DATA ENCODING FUNCTIONS
# ============================================================================

def angle_encoding(x: np.ndarray, wires: List[int]) -> None:
    """Encode classical data into rotation angles."""
    for i, xi in enumerate(x):
        qml.RY(xi, wires=wires[i])


def amplitude_encoding(x: np.ndarray, wires: List[int]) -> None:
    """Encode data into amplitudes of a quantum state (requires normalization)."""
    norm = np.linalg.norm(x)
    if norm < 1e-10:
        x = np.ones(len(x)) / np.sqrt(len(x))
    else:
        x = x / norm
    qml.AmplitudeEmbedding(features=x, wires=wires, normalize=True)


# ============================================================================
# FACTORY: Observable to circuit input
# ============================================================================

def observable_to_circuit_input(observable: Any, encoding: str = 'angle', max_features: int = 10) -> np.ndarray:
    """
    Convert a Layer 1 UltimateObservable to a feature vector suitable for quantum circuit encoding.

    Args:
        observable: An object with attributes like qualitative_dims (dict), relational_embedding (list or array),
                    atomicity_score (float). If not available, a random vector is returned.
        encoding: 'angle' or 'amplitude' – determines the required range (angle encoding expects values in [-π, π] typically).
        max_features: Maximum number of features to return (pad or truncate).

    Returns:
        A 1D numpy array of floats, ready for encoding.
    """
    features = []
    # Try to extract qualitative_dims
    if hasattr(observable, 'qualitative_dims') and observable.qualitative_dims:
        # assume values are numbers
        for v in observable.qualitative_dims.values():
            if isinstance(v, (int, float)):
                features.append(float(v))
    # Try relational_embedding
    if hasattr(observable, 'relational_embedding') and observable.relational_embedding is not None:
        emb = observable.relational_embedding
        if isinstance(emb, (list, tuple, np.ndarray)):
            for val in emb:
                if isinstance(val, (int, float)):
                    features.append(float(val))
    # Try atomicity_score
    if hasattr(observable, 'atomicity_score') and observable.atomicity_score is not None:
        features.append(float(observable.atomicity_score))

    # If no features found, return random noise (for fallback)
    if len(features) == 0:
        logger.warning("No features found in observable; returning random vector.")
        features = np.random.randn(max_features).tolist()

    # Pad or truncate to max_features
    if len(features) < max_features:
        features = features + [0.0] * (max_features - len(features))
    else:
        features = features[:max_features]

    return np.array(features)


# ============================================================================
# QUANTUM KERNEL (PennyLane)
# ============================================================================

if HAS_PENNYLANE:
    class QuantumKernel:
        """
        Quantum kernel for SVM using PennyLane.
        Computes the kernel matrix via fidelity between encoded states.
        For angle encoding, the kernel is the fidelity |⟨ψ(x1)|ψ(x2)⟩|², which is a valid quantum kernel.
        """
        def __init__(self, n_qubits: int, encoding: str = 'angle', device: str = 'default.qubit'):
            self.n_qubits = n_qubits
            self.encoding = encoding
            self.dev = qml.device(device, wires=n_qubits)
            self.kernel_fn = self._build_kernel()

        def _build_kernel(self):
            @qml.qnode(self.dev)
            def kernel_circuit(x1, x2):
                # Encode first vector
                if self.encoding == 'angle':
                    angle_encoding(x1, range(self.n_qubits))
                elif self.encoding == 'amplitude':
                    amplitude_encoding(x1, range(self.n_qubits))
                else:
                    raise ValueError(f"Unknown encoding: {self.encoding}")
                # Inverse encoding of second vector
                qml.adjoint(lambda: (
                    angle_encoding(x2, range(self.n_qubits)) if self.encoding == 'angle'
                    else amplitude_encoding(x2, range(self.n_qubits))
                ))
                return qml.probs(wires=range(self.n_qubits))

            def kernel(x1, x2):
                probs = kernel_circuit(x1, x2)
                # Fidelity is probability of |0...0> (first amplitude)
                return probs[0]
            return kernel

        def kernel_matrix(self, X1: np.ndarray, X2: Optional[np.ndarray] = None) -> np.ndarray:
            """Compute kernel matrix between X1 and X2 (if None, use X1)."""
            if X2 is None:
                X2 = X1
            n1, n2 = len(X1), len(X2)
            K = np.zeros((n1, n2))
            for i in range(n1):
                for j in range(n2):
                    K[i, j] = self.kernel_fn(X1[i], X2[j])
            return K

else:
    class QuantumKernel:
        def __init__(self, *args, **kwargs):
            raise ImportError("PennyLane is required for QuantumKernel")


# ============================================================================
# QSVM (using kernel with sklearn)
# ============================================================================

class QSVM(QuantumMLModel):
    """
    Quantum Support Vector Machine using a quantum kernel.
    Can use either PennyLane kernel (if available) or Qiskit's QSVC.
    """
    def __init__(self, backend: str = 'pennylane', **kwargs):
        super().__init__()
        self.backend = backend
        self.kwargs = kwargs
        self.model = None
        self.kernel = None

        if backend == 'pennylane':
            if not HAS_PENNYLANE:
                raise ImportError("PennyLane required for pennylane backend")
            if not HAS_SKLEARN:
                raise ImportError("scikit‑learn required for SVM")
            self.kernel = QuantumKernel(**kwargs)
            self.model = SVC(kernel=lambda X, Y: self.kernel.kernel_matrix(X, Y))
        elif backend == 'qiskit':
            if not HAS_QISKIT_ML:
                raise ImportError("Qiskit Machine Learning required for qiskit backend")
            # Use Qiskit's QSVC (which uses a quantum kernel)
            feature_map = ZZFeatureMap(feature_dimension=kwargs.get('n_features', 2), reps=2)
            self.kernel = FidelityQuantumKernel(feature_map=feature_map)
            self.model = QSVC(quantum_kernel=self.kernel)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model not fitted yet.")
        return self.model.predict(X)


# ============================================================================
# VARIATIONAL QUANTUM CLASSIFIER (standard circuit)
# ============================================================================

if HAS_PENNYLANE:
    class VariationalQuantumClassifier(QuantumMLModel):
        """
        Variational Quantum Classifier using PennyLane.
        Trains a parameterized circuit to classify data.
        """
        def __init__(self, n_qubits: int, n_layers: int = 2, encoding: str = 'angle',
                     device: str = 'default.qubit', optimizer: str = 'adam', steps: int = 100):
            super().__init__()
            self.n_qubits = n_qubits
            self.n_layers = n_layers
            self.encoding = encoding
            self.dev = qml.device(device, wires=n_qubits)
            self.optimizer_name = optimizer
            self.steps = steps
            self.params = None
            self.circuit = self._build_circuit()

        def _build_circuit(self):
            @qml.qnode(self.dev)
            def circuit(x, weights):
                # Encode data
                if self.encoding == 'angle':
                    angle_encoding(x, range(self.n_qubits))
                elif self.encoding == 'amplitude':
                    amplitude_encoding(x, range(self.n_qubits))
                else:
                    raise ValueError(f"Unknown encoding: {self.encoding}")
                # Variational layers
                for l in range(self.n_layers):
                    for i in range(self.n_qubits):
                        qml.RY(weights[l, i, 0], wires=i)
                        qml.RZ(weights[l, i, 1], wires=i)
                    for i in range(self.n_qubits - 1):
                        qml.CNOT(wires=[i, i+1])
                # Measurement (expectation value on first qubit)
                return qml.expval(qml.PauliZ(0))
            return circuit

        def fit(self, X: np.ndarray, y: np.ndarray):
            # Convert labels to ±1
            y_ = 2 * y - 1  # assume y in {0,1}
            n_samples = len(X)
            # Initialize weights
            self.params = pnp.random.randn(self.n_layers, self.n_qubits, 2, requires_grad=True)
            # Choose optimizer
            if self.optimizer_name == 'adam':
                opt = AdamOptimizer(stepsize=0.1)
            else:
                opt = NesterovMomentum(stepsize=0.1)

            # Training loop
            for step in range(self.steps):
                # Compute cost
                def cost(weights):
                    total = 0.0
                    for i in range(n_samples):
                        pred = self.circuit(X[i], weights)
                        total += (pred - y_[i]) ** 2
                    return total / n_samples
                self.params, loss = opt.step_and_cost(cost, self.params)
                if step % 20 == 0:
                    logger.debug(f"Step {step}, loss = {loss:.4f}")
            self.is_fitted = True
            return self

        def predict(self, X: np.ndarray) -> np.ndarray:
            if not self.is_fitted:
                raise RuntimeError("Model not fitted.")
            preds = []
            for i in range(len(X)):
                val = self.circuit(X[i], self.params)
                preds.append(1 if val > 0 else 0)
            return np.array(preds)

else:
    class VariationalQuantumClassifier(QuantumMLModel):
        def __init__(self, *args, **kwargs):
            raise ImportError("PennyLane is required for VariationalQuantumClassifier")


# ============================================================================
# DATA RE‑UPLOADING VARIATIONAL CLASSIFIER (increased expressivity)
# ============================================================================

if HAS_PENNYLANE:
    class DataReuploadingClassifier(QuantumMLModel):
        """
        Variational classifier with data re‑uploading.
        Data is encoded repeatedly between trainable layers.
        """
        def __init__(self, n_qubits: int, n_layers: int = 3, encoding: str = 'angle',
                     device: str = 'default.qubit', optimizer: str = 'adam', steps: int = 100):
            super().__init__()
            self.n_qubits = n_qubits
            self.n_layers = n_layers
            self.encoding = encoding
            self.dev = qml.device(device, wires=n_qubits)
            self.optimizer_name = optimizer
            self.steps = steps
            self.params = None
            self.circuit = self._build_circuit()

        def _build_circuit(self):
            @qml.qnode(self.dev)
            def circuit(x, weights):
                # Data re‑uploading: for each layer, encode data then apply trainable gates
                for l in range(self.n_layers):
                    # Data encoding
                    if self.encoding == 'angle':
                        angle_encoding(x, range(self.n_qubits))
                    elif self.encoding == 'amplitude':
                        amplitude_encoding(x, range(self.n_qubits))
                    else:
                        raise ValueError(f"Unknown encoding: {self.encoding}")
                    # Trainable layer
                    for i in range(self.n_qubits):
                        qml.RY(weights[l, i, 0], wires=i)
                        qml.RZ(weights[l, i, 1], wires=i)
                    for i in range(self.n_qubits - 1):
                        qml.CNOT(wires=[i, i+1])
                # Measurement (expectation value on first qubit)
                return qml.expval(qml.PauliZ(0))
            return circuit

        def fit(self, X: np.ndarray, y: np.ndarray):
            y_ = 2 * y - 1
            n_samples = len(X)
            self.params = pnp.random.randn(self.n_layers, self.n_qubits, 2, requires_grad=True)
            if self.optimizer_name == 'adam':
                opt = AdamOptimizer(stepsize=0.1)
            else:
                opt = NesterovMomentum(stepsize=0.1)

            for step in range(self.steps):
                def cost(weights):
                    total = 0.0
                    for i in range(n_samples):
                        pred = self.circuit(X[i], weights)
                        total += (pred - y_[i]) ** 2
                    return total / n_samples
                self.params, loss = opt.step_and_cost(cost, self.params)
                if step % 20 == 0:
                    logger.debug(f"Step {step}, loss = {loss:.4f}")
            self.is_fitted = True
            return self

        def predict(self, X: np.ndarray) -> np.ndarray:
            if not self.is_fitted:
                raise RuntimeError("Model not fitted.")
            preds = []
            for i in range(len(X)):
                val = self.circuit(X[i], self.params)
                preds.append(1 if val > 0 else 0)
            return np.array(preds)

else:
    class DataReuploadingClassifier(QuantumMLModel):
        def __init__(self, *args, **kwargs):
            raise ImportError("PennyLane required for DataReuploadingClassifier")


# ============================================================================
# QUANTUM GENERATIVE ADVERSARIAL NETWORK (QGAN)
# ============================================================================

if HAS_PENNYLANE and HAS_TORCH:
    class QuantumGenerator(nn.Module):
        """
        Quantum generator that uses a variational circuit to map latent vectors to samples.
        The circuit takes a latent vector (encoded into rotations) and outputs expectation values.
        """
        def __init__(self, n_qubits: int, n_latent: int, n_layers: int = 2,
                     device: str = 'default.qubit'):
            super().__init__()
            self.n_qubits = n_qubits
            self.n_latent = n_latent
            self.n_layers = n_layers
            self.dev = qml.device(device, wires=n_qubits)
            # Trainable parameters (weights for variational layers)
            # We'll store them as nn.Parameter for integration with PyTorch optimizer
            self.weights = nn.Parameter(torch.randn(n_layers, n_qubits, 2) * 0.1)
            # Create the QNode
            self.circuit = self._build_circuit()

        def _build_circuit(self):
            @qml.qnode(self.dev, interface='torch')
            def circuit(latent, weights):
                # Encode latent vector into rotations (angle encoding)
                for i in range(self.n_qubits):
                    if i < self.n_latent:
                        qml.RY(latent[i], wires=i)
                    else:
                        qml.RY(0.0, wires=i)  # pad with zeros
                # Variational layers
                for l in range(self.n_layers):
                    for i in range(self.n_qubits):
                        qml.RY(weights[l, i, 0], wires=i)
                        qml.RZ(weights[l, i, 1], wires=i)
                    for i in range(self.n_qubits - 1):
                        qml.CNOT(wires=[i, i+1])
                # Return expectation values on all qubits (as features)
                return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]
            return circuit

        def forward(self, latent):
            # latent: batch of latent vectors (batch_size, n_latent)
            batch_size = latent.shape[0]
            # Evaluate circuit for each sample in batch
            # We'll loop (or use qml.batch if available, but loop is simpler)
            outputs = []
            for i in range(batch_size):
                out = self.circuit(latent[i], self.weights)
                outputs.append(torch.stack(out))
            return torch.stack(outputs)  # (batch_size, n_qubits)


    class QGAN(QuantumMLModel):
        """
        Quantum Generative Adversarial Network.
        Uses a quantum generator (PennyLane) and a classical discriminator (PyTorch).
        """
        def __init__(self, n_qubits: int = 4, n_latent: int = 2, n_layers: int = 2,
                     device: str = 'default.qubit', lr: float = 0.001,
                     batch_size: int = 32, epochs: int = 100):
            super().__init__()
            self.n_qubits = n_qubits
            self.n_latent = n_latent
            self.batch_size = batch_size
            self.epochs = epochs
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            # Generator (quantum)
            self.generator = QuantumGenerator(n_qubits, n_latent, n_layers, device).to(self.device)

            # Discriminator (classical neural network)
            self.discriminator = nn.Sequential(
                nn.Linear(n_qubits, 64),
                nn.LeakyReLU(0.2),
                nn.Linear(64, 32),
                nn.LeakyReLU(0.2),
                nn.Linear(32, 1),
                nn.Sigmoid()
            ).to(self.device)

            # Optimizers
            self.optim_G = optim.Adam(self.generator.parameters(), lr=lr)
            self.optim_D = optim.Adam(self.discriminator.parameters(), lr=lr)

            # Loss
            self.criterion = nn.BCELoss()

            self.is_fitted = False

        def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
            """
            Train the QGAN on real data X (numpy array of shape (n_samples, n_qubits)).
            """
            # Convert data to torch tensor
            real_data = torch.tensor(X, dtype=torch.float32).to(self.device)
            dataset = TensorDataset(real_data)
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

            for epoch in range(self.epochs):
                for i, (real_batch,) in enumerate(dataloader):
                    batch_size = real_batch.size(0)

                    # Train Discriminator
                    # Real data
                    real_labels = torch.ones(batch_size, 1).to(self.device)
                    fake_labels = torch.zeros(batch_size, 1).to(self.device)

                    # Forward pass real
                    real_output = self.discriminator(real_batch)
                    loss_D_real = self.criterion(real_output, real_labels)

                    # Generate fake data
                    latent = torch.randn(batch_size, self.n_latent).to(self.device)
                    fake_data = self.generator(latent)
                    fake_output = self.discriminator(fake_data.detach())
                    loss_D_fake = self.criterion(fake_output, fake_labels)

                    loss_D = loss_D_real + loss_D_fake
                    self.optim_D.zero_grad()
                    loss_D.backward()
                    self.optim_D.step()

                    # Train Generator
                    latent = torch.randn(batch_size, self.n_latent).to(self.device)
                    fake_data = self.generator(latent)
                    fake_output = self.discriminator(fake_data)
                    loss_G = self.criterion(fake_output, real_labels)  # want to fool D

                    self.optim_G.zero_grad()
                    loss_G.backward()
                    self.optim_G.step()

                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Loss D: {loss_D.item():.4f}, Loss G: {loss_G.item():.4f}")

            self.is_fitted = True
            return self

        def generate(self, n_samples: int) -> np.ndarray:
            """Generate n_samples from the trained generator."""
            if not self.is_fitted:
                raise RuntimeError("Model not fitted.")
            self.generator.eval()
            with torch.no_grad():
                latent = torch.randn(n_samples, self.n_latent).to(self.device)
                samples = self.generator(latent).cpu().numpy()
            return samples

        def predict(self, X: np.ndarray) -> np.ndarray:
            # Not meaningful for GAN; return zeros
            return np.zeros(len(X))

else:
    class QGAN(QuantumMLModel):
        def __init__(self, *args, **kwargs):
            raise ImportError("QGAN requires PennyLane and PyTorch.")


# ============================================================================
# QUANTUM CIRCUIT LEARNING (REGRESSION) – already similar to classifier
# ============================================================================

class QuantumCircuitLearner(QuantumMLModel):
    """
    Quantum circuit learning for regression (predict continuous values).
    Uses a variational circuit with output expectation value.
    """
    def __init__(self, n_qubits: int, n_layers: int = 2, encoding: str = 'angle',
                 device: str = 'default.qubit', optimizer: str = 'adam', steps: int = 100):
        if not HAS_PENNYLANE:
            raise ImportError("PennyLane required for QuantumCircuitLearner")
        super().__init__()
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.encoding = encoding
        self.dev = qml.device(device, wires=n_qubits)
        self.optimizer_name = optimizer
        self.steps = steps
        self.params = None
        self.circuit = self._build_circuit()

    def _build_circuit(self):
        @qml.qnode(self.dev)
        def circuit(x, weights):
            # Encode data
            if self.encoding == 'angle':
                angle_encoding(x, range(self.n_qubits))
            elif self.encoding == 'amplitude':
                amplitude_encoding(x, range(self.n_qubits))
            else:
                raise ValueError(f"Unknown encoding: {self.encoding}")
            # Variational layers
            for l in range(self.n_layers):
                for i in range(self.n_qubits):
                    qml.RY(weights[l, i, 0], wires=i)
                    qml.RZ(weights[l, i, 1], wires=i)
                for i in range(self.n_qubits - 1):
                    qml.CNOT(wires=[i, i+1])
            # Measurement (expectation value on first qubit)
            return qml.expval(qml.PauliZ(0))
        return circuit

    def fit(self, X: np.ndarray, y: np.ndarray):
        if not HAS_PENNYLANE:
            raise ImportError("PennyLane required for QuantumCircuitLearner")
        n_samples = len(X)
        self.params = pnp.random.randn(self.n_layers, self.n_qubits, 2, requires_grad=True)
        if self.optimizer_name == 'adam':
            opt = AdamOptimizer(stepsize=0.1)
        else:
            opt = NesterovMomentum(stepsize=0.1)

        for step in range(self.steps):
            def cost(weights):
                total = 0.0
                for i in range(n_samples):
                    pred = self.circuit(X[i], weights)
                    total += (pred - y[i]) ** 2
                return total / n_samples
            self.params, loss = opt.step_and_cost(cost, self.params)
            if step % 20 == 0:
                logger.debug(f"Step {step}, loss = {loss:.4f}")
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        preds = []
        for i in range(len(X)):
            preds.append(self.circuit(X[i], self.params))
        return np.array(preds)


# ============================================================================
# UTILITY: ENSURE IMPORTS
# ============================================================================

def check_available():
    """Print which quantum libraries are available."""
    print("PennyLane available:", HAS_PENNYLANE)
    print("Qiskit ML available:", HAS_QISKIT_ML)
    print("scikit‑learn available:", HAS_SKLEARN)
    print("PyTorch available:", HAS_TORCH)


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Run a simple demo with synthetic data."""
    if not HAS_SKLEARN:
        print("scikit‑learn required for demo.")
        return

    from sklearn.datasets import make_classification, make_regression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    # Classification data
    X_cls, y_cls = make_classification(n_samples=100, n_features=2, n_redundant=0,
                                        n_clusters_per_class=1, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X_cls, y_cls, test_size=0.3, random_state=42)

    # Scale data to [-1, 1] for angle encoding
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Try PennyLane QSVM
    if HAS_PENNYLANE and HAS_SKLEARN:
        print("\n--- PennyLane QSVM ---")
        try:
            qsvm = QSVM(backend='pennylane', n_qubits=2, encoding='angle')
            qsvm.fit(X_train, y_train)
            acc = qsvm.score(X_test, y_test)
            print(f"Test accuracy: {acc:.3f}")
        except Exception as e:
            print(f"Error: {e}")

    # Try Variational Quantum Classifier (if PennyLane)
    if HAS_PENNYLANE:
        print("\n--- Variational Quantum Classifier ---")
        try:
            vqc = VariationalQuantumClassifier(n_qubits=2, n_layers=2, steps=50)
            vqc.fit(X_train[:20], y_train[:20])  # small for speed
            acc = vqc.score(X_test[:10], y_test[:10])
            print(f"Test accuracy (small sample): {acc:.3f}")
        except Exception as e:
            print(f"Error: {e}")

    # Try Data Re‑uploading Classifier
    if HAS_PENNYLANE:
        print("\n--- Data Re‑uploading Classifier ---")
        try:
            dru = DataReuploadingClassifier(n_qubits=2, n_layers=3, steps=50)
            dru.fit(X_train[:20], y_train[:20])
            acc = dru.score(X_test[:10], y_test[:10])
            print(f"Test accuracy (small sample): {acc:.3f}")
        except Exception as e:
            print(f"Error: {e}")

    # Try Qiskit QSVM if available
    if HAS_QISKIT_ML:
        print("\n--- Qiskit QSVM ---")
        try:
            qsvm_q = QSVM(backend='qiskit', n_features=2)
            qsvm_q.fit(X_train, y_train)
            acc = qsvm_q.score(X_test, y_test)
            print(f"Test accuracy: {acc:.3f}")
        except Exception as e:
            print(f"Error: {e}")

    # QGAN demo (if torch and pennylane available)
    if HAS_PENNYLANE and HAS_TORCH:
        print("\n--- QGAN ---")
        # Generate synthetic 2D data (e.g., from a mixture of Gaussians)
        np.random.seed(42)
        real_data = np.vstack([
            np.random.randn(500, 2) * 0.5 + [2, 2],
            np.random.randn(500, 2) * 0.5 + [-2, -2]
        ])
        # Scale to approx [-1,1]
        real_data = real_data / 3.0

        qgan = QGAN(n_qubits=2, n_latent=2, epochs=20, batch_size=32)
        qgan.fit(real_data)
        fake = qgan.generate(10)
        print("Generated samples (first 5):\n", fake[:5])
    else:
        print("\n--- QGAN skipped (requires PennyLane and PyTorch) ---")

    # Quantum Circuit Learner for regression
    if HAS_PENNYLANE:
        print("\n--- Quantum Circuit Learner (Regression) ---")
        X_reg, y_reg = make_regression(n_samples=50, n_features=2, noise=0.1, random_state=42)
        X_reg = scaler.fit_transform(X_reg)
        y_reg = (y_reg - y_reg.mean()) / y_reg.std()  # normalize
        Xr_train, Xr_test, yr_train, yr_test = train_test_split(X_reg, y_reg, test_size=0.3, random_state=42)
        qcl = QuantumCircuitLearner(n_qubits=2, n_layers=2, steps=50)
        qcl.fit(Xr_train[:20], yr_train[:20])
        pred = qcl.predict(Xr_test[:5])
        print("Predictions (first 5):", pred)
        print("True values:", yr_test[:5])


if __name__ == "__main__":
    demo()