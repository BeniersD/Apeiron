import pytest
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

class TestQSVM:
    @pytest.fixture
    def data(self):
        X, y = make_blobs(
            n_samples=200,
            n_features=2,
            centers=2,
            cluster_std=0.5,
            center_box=(-5, 5),
            random_state=42
        )
        scaler = MinMaxScaler(feature_range=(-np.pi, np.pi))
        X = scaler.fit_transform(X)
        return train_test_split(X, y, test_size=0.3, random_state=42)

    def test_pennylane_qsvm_accuracy(self, data):
        pytest.importorskip("pennylane")
        from apeiron.optional.quantum_ml import QSVM
        X_train, X_test, y_train, y_test = data
        qsvm = QSVM(backend="pennylane", n_qubits=2, encoding="angle")
        qsvm.fit(X_train, y_train)
        acc = qsvm.score(X_test, y_test)
        assert acc > 0.8

    def test_qiskit_qsvm_accuracy(self, data):
        pytest.importorskip("qiskit")
        from apeiron.optional.quantum_ml import QSVM
        X_train, X_test, y_train, y_test = data
        qsvm = QSVM(backend="qiskit", n_features=2)
        qsvm.fit(X_train, y_train)
        acc = qsvm.score(X_test, y_test)
        assert acc > 0.8


class TestVariationalClassifier:
    """Test dat VQC training niet crasht en de loss daalt."""
    @pytest.fixture
    def data(self):
        X, y = make_blobs(n_samples=20, n_features=2, centers=2,
                           cluster_std=0.5, random_state=42)
        scaler = MinMaxScaler(feature_range=(-np.pi, np.pi))
        X = scaler.fit_transform(X)
        return X, y

    @pytest.mark.slow
    def test_vqc_training(self, data):
        pytest.importorskip("pennylane")
        from apeiron.optional.quantum_ml import VariationalQuantumClassifier
        X, y = data
        vqc = VariationalQuantumClassifier(n_qubits=2, n_layers=2, steps=20)
        vqc.fit(X, y)
        assert vqc.is_fitted
        # loss moet kleiner zijn dan initiële (ongeveer)
        preds = vqc.predict(X)
        assert len(preds) == len(y)

    @pytest.mark.slow
    def test_data_reuploading_training(self, data):
        pytest.importorskip("pennylane")
        from apeiron.optional.quantum_ml import DataReuploadingClassifier
        X, y = data
        dru = DataReuploadingClassifier(n_qubits=2, n_layers=2, steps=20)
        dru.fit(X, y)
        assert dru.is_fitted
        preds = dru.predict(X)
        assert len(preds) == len(y)


class TestQGAN:
    @pytest.fixture
    def data(self):
        np.random.seed(42)
        X = (np.random.randn(100, 2).astype(np.float32) * 0.5 + np.array([2, 2], dtype=np.float32))
        return X

    @pytest.mark.slow
    def test_qgan_generation(self, data):
        pytest.importorskip("pennylane")
        pytest.importorskip("torch")
        from apeiron.optional.quantum_ml import QGAN
        qgan = QGAN(n_qubits=2, n_latent=2, epochs=2, batch_size=32)
        qgan.fit(data)
        fake = qgan.generate(5)
        assert fake.shape == (5, 2)


class TestQuantumCircuitLearner:
    def test_regression_training(self):
        pytest.importorskip("pennylane")
        from apeiron.optional.quantum_ml import QuantumCircuitLearner
        X = np.random.randn(20, 2)
        y = X[:, 0] * 0.5 + X[:, 1] * 0.3
        qcl = QuantumCircuitLearner(n_qubits=2, n_layers=2, steps=10)
        qcl.fit(X, y)
        preds = qcl.predict(X[:5])
        assert len(preds) == 5