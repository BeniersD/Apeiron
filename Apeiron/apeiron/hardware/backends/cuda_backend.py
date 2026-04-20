"""
CUDA/GPU Backend - PyTorch-based GPU acceleration.
Provides massive parallelism for field operations.
"""

import numpy as np
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional

from .backend import HardwareBackend

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class CUDABackend(HardwareBackend):
    """
    CUDA/GPU backend using PyTorch for acceleration.
    All operations are vectorized and run on the GPU when available.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "CUDA"
        self.device = None
        self.is_available = TORCH_AVAILABLE and torch.cuda.is_available()
        
        # O(1) lookups via dictionaries
        self.fields: Dict[int, torch.Tensor] = {}
        self.field_data: Dict[int, np.ndarray] = {}
        self.field_hash: Dict[str, int] = {}
        self._next_id = 0
        
        self.config = {
            'device_id': 0,
            'memory_fraction': 0.8,
            'use_tensor_cores': True,
        }
        
        self.metrics = {
            'total_operations': 0,
            'total_gpu_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
        
        self.logger = logging.getLogger('CUDA')
        if self.is_available:
            self.logger.info(f"🎮 CUDA Backend - {torch.cuda.get_device_name(0)}")
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        if not self.is_available:
            self.logger.warning("CUDA not available")
            return False
        
        self.config.update(config)
        device_id = self.config.get('device_id', 0)
        self.device = torch.device(f'cuda:{device_id}')
        
        if 'memory_fraction' in self.config:
            torch.cuda.set_per_process_memory_fraction(self.config['memory_fraction'])
        
        self.logger.info(f"✅ CUDA initialized on {torch.cuda.get_device_name(device_id)}")
        return True
    
    def create_continuous_field(self, dimensions: int) -> np.ndarray:
        field = np.random.randn(dimensions).astype(np.float32)
        field = field / np.linalg.norm(field)
        
        tensor = torch.from_numpy(field).to(self.device)
        
        field_id = self._next_id
        self._next_id += 1
        self.fields[field_id] = tensor
        self.field_data[field_id] = field
        
        field_hash = hashlib.md5(field.tobytes()).hexdigest()
        self.field_hash[field_hash] = field_id
        
        return field
    
    def get_field_id(self, field: np.ndarray) -> Optional[int]:
        try:
            field_hash = hashlib.md5(field.tobytes()).hexdigest()
            if field_hash in self.field_hash:
                self.metrics['cache_hits'] += 1
                return self.field_hash[field_hash]
        except:
            pass
        
        self.metrics['cache_misses'] += 1
        for fid, stored in self.field_data.items():
            if np.array_equal(stored, field):
                try:
                    field_hash = hashlib.md5(field.tobytes()).hexdigest()
                    self.field_hash[field_hash] = fid
                except:
                    pass
                return fid
        return None
    
    def field_update(self, field: np.ndarray, dt: float,
                    verleden: np.ndarray, heden: np.ndarray,
                    toekomst: np.ndarray) -> Dict[str, np.ndarray]:
        start = time.time()
        
        fid = self._get_or_create_tensor(field)
        vid = self._get_or_create_tensor(verleden)
        hid = self._get_or_create_tensor(heden)
        tid = self._get_or_create_tensor(toekomst)
        
        f_tensor = self.fields[fid]
        v_tensor = self.fields[vid]
        h_tensor = self.fields[hid]
        t_tensor = self.fields[tid]
        
        with torch.no_grad():
            v_new = v_tensor * 0.95 + h_tensor * 0.05
            t_new = t_tensor * 0.97 + h_tensor * 0.03
            h_new = f_tensor + 0.01 * torch.randn_like(f_tensor) * np.sqrt(dt)
            h_new = h_new / torch.norm(h_new)
        
        self.fields[vid] = v_new
        self.fields[tid] = t_new
        self.fields[fid] = h_new
        
        self.field_data[vid] = v_new.cpu().numpy()
        self.field_data[tid] = t_new.cpu().numpy()
        self.field_data[fid] = h_new.cpu().numpy()
        
        self.metrics['total_operations'] += 1
        self.metrics['total_gpu_time'] += time.time() - start
        
        return {
            'verleden': self.field_data[vid],
            'heden': self.field_data[fid],
            'toekomst': self.field_data[tid]
        }
    
    def _get_or_create_tensor(self, array: np.ndarray) -> int:
        fid = self.get_field_id(array)
        if fid is not None:
            return fid
        
        tensor = torch.from_numpy(array.astype(np.float32)).to(self.device)
        fid = self._next_id
        self._next_id += 1
        self.fields[fid] = tensor
        self.field_data[fid] = array.copy()
        return fid
    
    def compute_interference(self, a: np.ndarray, b: np.ndarray) -> float:
        aid = self._get_or_create_tensor(a)
        bid = self._get_or_create_tensor(b)
        
        a_tensor = self.fields[aid]
        b_tensor = self.fields[bid]
        
        with torch.no_grad():
            a_norm = a_tensor / torch.norm(a_tensor)
            b_norm = b_tensor / torch.norm(b_tensor)
            result = torch.dot(a_norm, b_norm).item()
        
        return max(0.0, min(1.0, result))
    
    def find_stable_patterns(self, fields: List[np.ndarray],
                            threshold: float) -> List[Dict]:
        n = len(fields)
        results = []
        for i in range(n):
            for j in range(i+1, n):
                strength = self.compute_interference(fields[i], fields[j])
                if strength >= threshold:
                    results.append({
                        'i': i, 'j': j,
                        'sterkte': strength,
                        'veld': (fields[i] + fields[j]) / np.linalg.norm(fields[i] + fields[j])
                    })
        return sorted(results, key=lambda x: x['sterkte'], reverse=True)
    
    def measure_coherence(self, fields: List[np.ndarray]) -> float:
        if len(fields) < 2:
            return 1.0
        
        ids = [self._get_or_create_tensor(f) for f in fields]
        tensors = torch.stack([self.fields[i] for i in ids])
        
        with torch.no_grad():
            gram = tensors @ tensors.T
            n = len(fields)
            coherence = (gram.sum().item() - n) / (n * (n - 1))
        
        return max(0.0, min(1.0, coherence))
    
    def get_info(self) -> str:
        if self.is_available:
            return f"CUDA ({torch.cuda.get_device_name(0)}) - {len(self.fields)} fields"
        return "CUDA (not available)"
    
    def cleanup(self):
        self.fields.clear()
        self.field_data.clear()
        self.field_hash.clear()
        self._next_id = 0
        if self.is_available:
            torch.cuda.empty_cache()
        self.logger.info("🧹 CUDA resources cleaned")