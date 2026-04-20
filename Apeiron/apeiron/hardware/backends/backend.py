"""
Abstract base class for all hardware backends.
Defines the interface that every backend must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class HardwareBackend(ABC):
    """
    Abstract base class for hardware backends (CPU, CUDA, FPGA, Quantum).
    
    All concrete backends must implement these methods to ensure
    a uniform interface for the hardware factory.
    """
    
    def __init__(self):
        self.name = "Abstract"
        self.is_available = False
        self.metrics = {}
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the backend with given configuration."""
        pass
    
    @abstractmethod
    def create_continuous_field(self, dimensions: int) -> np.ndarray:
        """Create a continuous field of given dimensions."""
        pass
    
    @abstractmethod
    def field_update(self, field: np.ndarray, dt: float,
                    verleden: np.ndarray, heden: np.ndarray,
                    toekomst: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Update a field using hardware acceleration.
        
        Returns:
            Dict with keys 'verleden', 'heden', 'toekomst'.
        """
        pass
    
    @abstractmethod
    def compute_interference(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute interference (dot product) between two fields."""
        pass
    
    @abstractmethod
    def find_stable_patterns(self, fields: List[np.ndarray],
                            threshold: float) -> List[Dict]:
        """
        Find stable patterns among a list of fields.
        
        Returns:
            List of dicts with keys 'i', 'j', 'sterkte', 'veld'.
        """
        pass
    
    @abstractmethod
    def measure_coherence(self, fields: List[np.ndarray]) -> float:
        """Measure the overall coherence of a set of fields."""
        pass
    
    def get_info(self) -> str:
        """Return a human-readable info string."""
        return f"{self.name} backend"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return performance metrics collected by this backend."""
        return self.metrics
    
    def cleanup(self):
        """Release any resources held by the backend."""
        pass