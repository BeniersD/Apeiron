## 🧪 Running Tests

The framework includes comprehensive test suites for all components.

```bash
# Run all tests
pytest

# Run only Layer 1 tests
pytest apeiron/layers/layer01_foundational/tests/

# Run only hardware tests
pytest apeiron/tests/test_hardware.py

# Run with coverage report
pytest --cov=apeiron --cov-report=html