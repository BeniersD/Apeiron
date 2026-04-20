from setuptools import setup, find_packages

setup(
    name="apeiron",
    version="1.0.0",
    packages=find_packages(),
    description="Apeiron Framework – Non‑antropocentrische kennisgenese",
    author="David Beniers",
    license="MIT",
    python_requires=">=3.10",
    install_requires=[
        # Kernafhankelijkheden (altijd nodig)
        "numpy>=1.21.0",
        "psutil>=5.8.0",
    ],
    extras_require={
        'hardware': ['cupy', 'numba', 'pyopencl'],
        'cache': ['redis>=4.0.0'],
        'metrics': ['prometheus-client>=0.10.0'],
        'validation': ['pydantic>=2.0.0'],
        'distributed': ['ray>=2.0.0'],
        'quantum': ['qiskit>=0.40.0'],
        'image': ['scikit-image>=0.19.0'],
        'topology': ['gudhi>=3.5.0'],
        'all': [
            'redis>=4.0.0',
            'prometheus-client>=0.10.0',
            'pydantic>=2.0.0',
            'ray>=2.0.0',
            'qiskit>=0.40.0',
            'scikit-image>=0.19.0',
            'gudhi>=3.5.0',
            'psutil>=5.8.0',
            'cryptography>=3.4.0',
        ]
    }
)