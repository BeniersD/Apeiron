"""
HARDWARE CONFIGURATIE - UITGEBREIDE VERSIE
================================================================
Centrale configuratie voor alle hardware backends met type-veilige validatie.
Ondersteunt zowel Pydantic (als geïnstalleerd) als een dictionary fallback.

Uitbreidingen:
- Config versioning
- Config migratie
- Config diff/merge
- Validatie hooks
- Export naar meerdere formaten
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List, Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ====================================================================
# PYDANTIC IMPORT (OPTIONEEL)
# ====================================================================

try:
    from pydantic import BaseModel, Field, validator, ValidationError
    PYDANTIC_AVAILABLE = True
    logger.info("✅ Pydantic beschikbaar voor hardware configuratie")
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("⚠️ Pydantic niet geïnstalleerd - gebruik dictionary fallback")
    
    # Fallback classes (uitgebreid)
    class BaseModel:
        """Fallback BaseModel met extra functionaliteit"""
        def __init__(self, **kwargs):
            self._extra_fields = {}
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    self._extra_fields[key] = value
        
        def dict(self) -> Dict[str, Any]:
            """Converteer naar dictionary"""
            result = {}
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    if hasattr(value, 'dict'):
                        result[key] = value.dict()
                    else:
                        result[key] = value
            # Voeg extra velden toe
            result.update(self._extra_fields)
            return result
        
        def json(self, **kwargs) -> str:
            """Exporteer als JSON"""
            return json.dumps(self.dict(), **kwargs)
    
    def Field(default=None, **kwargs):
        """Fallback Field functie"""
        return default
    
    def validator(*args, **kwargs):
        """Fallback validator decorator"""
        def decorator(func):
            return func
        return decorator


# ====================================================================
# CONFIG VERSIE BEHEER
# ====================================================================

class ConfigVersion:
    """Configuratie versie beheer."""
    
    CURRENT_VERSION = "2.0"
    SUPPORTED_VERSIONS = ["1.0", "2.0"]
    
    @classmethod
    def migrate(cls, config_dict: Dict[str, Any], 
                from_version: str, 
                to_version: str = CURRENT_VERSION) -> Dict[str, Any]:
        """Migreer configuratie van oude naar nieuwe versie."""
        if from_version == to_version:
            return config_dict
        
        logger.info(f"🔄 Migreer config van v{from_version} naar v{to_version}")
        
        # Versie 1.0 -> 2.0 migratie
        if from_version == "1.0" and to_version == "2.0":
            return cls._migrate_v1_to_v2(config_dict)
        
        raise ValueError(f"Migratie van v{from_version} naar v{to_version} niet ondersteund")
    
    @classmethod
    def _migrate_v1_to_v2(cls, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Migreer v1.0 naar v2.0."""
        v2_config = {
            'backend': config_dict.get('backend', 'auto'),
            'fallback_to_cpu': config_dict.get('fallback_to_cpu', True),
            'log_level': config_dict.get('log_level', 'INFO'),
            'profile': config_dict.get('profile', False),
            'version': '2.0'
        }
        
        # CPU migratie
        cpu_old = config_dict.get('cpu', {})
        v2_config['cpu'] = {
            'precision': cpu_old.get('precision', 'float64'),
            'simulate_analog': cpu_old.get('simulate_analog', True),
            'num_threads': cpu_old.get('num_threads', 4),
            'use_blas': cpu_old.get('use_blas', True)
        }
        
        # CUDA migratie (nieuw in v2)
        cuda_old = config_dict.get('cuda', {})
        v2_config['cuda'] = {
            'device_id': cuda_old.get('device_id', 0),
            'memory_fraction': cuda_old.get('memory_fraction', 0.8),
            'use_tensor_cores': cuda_old.get('use_tensor_cores', True),
            'cudnn_benchmark': cuda_old.get('cudnn_benchmark', True),
            'allow_growth': cuda_old.get('allow_growth', False)
        }
        
        # FPGA migratie
        fpga_old = config_dict.get('fpga', {})
        v2_config['fpga'] = {
            'bitstream': fpga_old.get('bitstream', 'apeiron.bit'),
            'timeout': fpga_old.get('timeout', 1.0),
            'use_interrupts': fpga_old.get('use_interrupts', True),
            'dma_channels': fpga_old.get('dma_channels', 4),
            'clock_frequency': fpga_old.get('clock_frequency', None),
            'use_dual_port': fpga_old.get('use_dual_port', True)
        }
        
        # Quantum migratie
        quantum_old = config_dict.get('quantum', {})
        v2_config['quantum'] = {
            'n_qubits': quantum_old.get('n_qubits', 20),
            'shots': quantum_old.get('shots', 1000),
            'use_real_hardware': quantum_old.get('use_real_hardware', False),
            'backend_name': quantum_old.get('backend_name', 'aer_simulator'),
            'optimization_level': quantum_old.get('optimization_level', 1),
            'noise_model': quantum_old.get('noise_model', True),
            'coupling_map': quantum_old.get('coupling_map', False),
            'initial_layout': quantum_old.get('initial_layout', None)
        }
        
        return v2_config


# ====================================================================
# CPU CONFIGURATIE (UITGEBREID)
# ====================================================================

class CPUConfig(BaseModel):
    """
    CPU backend configuratie - UITGEBREID.
    
    Attributes:
        precision: Floating point precisie ('float32' of 'float64')
        simulate_analog: Simuleer analoge continuïteit
        num_threads: Aantal threads voor parallelle verwerking
        use_blas: Gebruik geoptimaliseerde BLAS bibliotheken
        cpu_affinity: CPU affiniteit (lijst van cores)
        use_avx: Gebruik AVX instructies
        use_sse: Gebruik SSE instructies
        vector_size: Vector grootte voor SIMD
        cache_size: CPU cache grootte in KB
    """
    precision: str = Field(
        default="float64",
        description="Floating point precisie: 'float32' of 'float64'"
    )
    simulate_analog: bool = Field(
        default=True,
        description="Simuleer analoge continuïteit"
    )
    num_threads: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Aantal threads voor parallelle verwerking"
    )
    use_blas: bool = Field(
        default=True,
        description="Gebruik geoptimaliseerde BLAS bibliotheken"
    )
    cpu_affinity: Optional[List[int]] = Field(
        default=None,
        description="CPU affiniteit (lijst van cores)"
    )
    use_avx: bool = Field(
        default=True,
        description="Gebruik AVX instructies"
    )
    use_sse: bool = Field(
        default=True,
        description="Gebruik SSE instructies"
    )
    vector_size: int = Field(
        default=256,
        ge=128,
        le=512,
        description="Vector grootte voor SIMD"
    )
    cache_size: Optional[int] = Field(
        default=None,
        description="CPU cache grootte in KB"
    )
    
    if PYDANTIC_AVAILABLE:
        @validator('precision')
        def validate_precision(cls, v):
            """Valideer precisie waarde"""
            if v not in ['float32', 'float64']:
                raise ValueError(f"Precisie moet 'float32' of 'float64' zijn, niet {v}")
            return v
        
        @validator('num_threads')
        def validate_threads(cls, v):
            """Valideer aantal threads"""
            try:
                import multiprocessing
                max_threads = multiprocessing.cpu_count()
                if v > max_threads:
                    logger.warning(f"Aantal threads ({v}) > beschikbare cores ({max_threads})")
                    return max_threads
            except:
                pass
            return v
        
        @validator('cpu_affinity')
        def validate_affinity(cls, v, values):
            """Valideer CPU affiniteit"""
            if v is not None:
                try:
                    import multiprocessing
                    max_cores = multiprocessing.cpu_count()
                    for core in v:
                        if core < 0 or core >= max_cores:
                            raise ValueError(f"Core {core} bestaat niet (max {max_cores-1})")
                except:
                    pass
            return v


# ====================================================================
# CUDA/GPU CONFIGURATIE (UITGEBREID)
# ====================================================================

class CUDAConfig(BaseModel):
    """
    CUDA/GPU backend configuratie - UITGEBREID.
    
    Attributes:
        device_id: GPU device ID (0 = eerste GPU)
        memory_fraction: Fractie van GPU geheugen om te gebruiken
        use_tensor_cores: Gebruik Tensor Cores
        cudnn_benchmark: Gebruik cuDNN benchmark
        allow_growth: Laat GPU geheugen groeien
        mixed_precision: Gebruik mixed precision training
        use_multi_gpu: Gebruik meerdere GPU's
        device_ids: Lijst van GPU device IDs bij multi-GPU
        sync_mode: Synchronisatie mode ('sync', 'async', 'stream')
        max_split_size: Max split size voor geheugen
    """
    device_id: int = Field(
        default=0,
        ge=0,
        description="GPU device ID (0 = eerste GPU)"
    )
    memory_fraction: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="Fractie van GPU geheugen om te gebruiken"
    )
    use_tensor_cores: bool = Field(
        default=True,
        description="Gebruik Tensor Cores"
    )
    cudnn_benchmark: bool = Field(
        default=True,
        description="Gebruik cuDNN benchmark"
    )
    allow_growth: bool = Field(
        default=False,
        description="Laat GPU geheugen groeien"
    )
    mixed_precision: bool = Field(
        default=False,
        description="Gebruik mixed precision training"
    )
    use_multi_gpu: bool = Field(
        default=False,
        description="Gebruik meerdere GPU's"
    )
    device_ids: List[int] = Field(
        default=[0],
        description="Lijst van GPU device IDs bij multi-GPU"
    )
    sync_mode: str = Field(
        default="async",
        description="Synchronisatie mode ('sync', 'async', 'stream')"
    )
    max_split_size: Optional[int] = Field(
        default=None,
        description="Max split size voor geheugen"
    )
    
    if PYDANTIC_AVAILABLE:
        @validator('device_id')
        def validate_device(cls, v):
            """Valideer dat GPU device bestaat"""
            try:
                import torch
                if v >= torch.cuda.device_count():
                    logger.warning(f"GPU device {v} niet beschikbaar, gebruik device 0")
                    return 0
            except:
                pass
            return v
        
        @validator('device_ids')
        def validate_device_ids(cls, v, values):
            """Valideer multi-GPU device IDs"""
            if values.get('use_multi_gpu', False):
                try:
                    import torch
                    available = torch.cuda.device_count()
                    for dev_id in v:
                        if dev_id >= available:
                            logger.warning(f"GPU {dev_id} niet beschikbaar")
                            return [0]
                except:
                    pass
            return v
        
        @validator('sync_mode')
        def validate_sync_mode(cls, v):
            """Valideer synchronisatie mode"""
            valid_modes = ['sync', 'async', 'stream']
            if v not in valid_modes:
                raise ValueError(f"sync_mode moet één van {valid_modes} zijn")
            return v


# ====================================================================
# FPGA CONFIGURATIE (UITGEBREID)
# ====================================================================

class FPGAConfig(BaseModel):
    """
    FPGA backend configuratie - UITGEBREID.
    
    Attributes:
        bitstream: Pad naar FPGA bitstream bestand
        timeout: Timeout voor hardware operaties
        use_interrupts: Gebruik interrupts voor synchronisatie
        dma_channels: Aantal DMA kanalen
        clock_frequency: FPGA klokfrequentie in MHz
        use_dual_port: Gebruik dual-port geheugen
        parallel_fields: Aantal parallelle velden
        monitor_temperature: Monitor FPGA temperatuur
        max_temperature: Maximale temperatuur in °C
        power_saving: Power saving mode
        max_power_watts: Maximaal power verbruik
        bitstream_version: Versie van bitstream
        fpga_family: FPGA familie (Kintex, Virtex, etc.)
    """
    bitstream: str = Field(
        default="apeiron.bit",
        description="Pad naar FPGA bitstream bestand"
    )
    timeout: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Timeout voor hardware operaties"
    )
    use_interrupts: bool = Field(
        default=True,
        description="Gebruik interrupts voor synchronisatie"
    )
    dma_channels: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Aantal DMA kanalen"
    )
    clock_frequency: Optional[float] = Field(
        default=None,
        description="FPGA klokfrequentie in MHz"
    )
    use_dual_port: bool = Field(
        default=True,
        description="Gebruik dual-port geheugen"
    )
    parallel_fields: int = Field(
        default=16,
        ge=1,
        le=64,
        description="Aantal parallelle velden"
    )
    monitor_temperature: bool = Field(
        default=True,
        description="Monitor FPGA temperatuur"
    )
    max_temperature: float = Field(
        default=85.0,
        ge=0.0,
        le=125.0,
        description="Maximale temperatuur in °C"
    )
    power_saving: bool = Field(
        default=False,
        description="Power saving mode"
    )
    max_power_watts: Optional[float] = Field(
        default=None,
        description="Maximaal power verbruik"
    )
    bitstream_version: str = Field(
        default="1.0",
        description="Versie van bitstream"
    )
    fpga_family: str = Field(
        default="Kintex",
        description="FPGA familie"
    )
    
    if PYDANTIC_AVAILABLE:
        @validator('bitstream')
        def bitstream_must_exist(cls, v):
            """Controleer of bitstream bestand bestaat"""
            if not os.path.exists(v):
                logger.warning(f"Bitstream {v} niet gevonden, gebruik standaard")
                return "apeiron.bit"
            return v


# ====================================================================
# QUANTUM CONFIGURATIE (UITGEBREID)
# ====================================================================

class QuantumConfig(BaseModel):
    """
    Quantum backend configuratie - UITGEBREID.
    
    Attributes:
        n_qubits: Aantal qubits
        shots: Aantal metingen
        use_real_hardware: Gebruik echte quantum hardware
        backend_name: Naam van quantum backend
        optimization_level: Optimalisatie niveau
        noise_model: Gebruik ruis model
        coupling_map: Gebruik echte qubit verbindingen
        initial_layout: Initiële qubit layout
        use_entanglement: Gebruik verstrengeling
        max_circuit_depth: Maximale circuit diepte
        error_mitigation: Error mitigation techniek
        min_quantum_volume: Minimum quantum volume
        shots_distribution: Verdeling van shots
        gate_fidelities: Gate fidelities per type
        measurement_errors: Meetfouten per qubit
    """
    n_qubits: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Aantal qubits"
    )
    shots: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Aantal metingen"
    )
    use_real_hardware: bool = Field(
        default=False,
        description="Gebruik echte quantum hardware"
    )
    backend_name: str = Field(
        default="aer_simulator",
        description="Naam van quantum backend",
        pattern="^(aer_simulator|ibmq_.*|qasm_simulator|statevector_simulator)$"
    )
    optimization_level: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Optimalisatie niveau"
    )
    noise_model: bool = Field(
        default=True,
        description="Gebruik ruis model"
    )
    coupling_map: bool = Field(
        default=False,
        description="Gebruik echte qubit verbindingen"
    )
    initial_layout: Optional[List[int]] = Field(
        default=None,
        description="Initiële qubit layout"
    )
    use_entanglement: bool = Field(
        default=True,
        description="Gebruik verstrengeling"
    )
    max_circuit_depth: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximale circuit diepte"
    )
    error_mitigation: str = Field(
        default="zero_noise_extrapolation",
        description="Error mitigation techniek",
        pattern="^(none|zero_noise_extrapolation|probabilistic_error_cancellation|richardson_extrapolation)$"
    )
    min_quantum_volume: int = Field(
        default=8,
        ge=1,
        le=1000,
        description="Minimum quantum volume"
    )
    shots_distribution: Dict[str, float] = Field(
        default_factory=lambda: {"baseline": 0.5, "mitigated": 0.5},
        description="Verdeling van shots"
    )
    gate_fidelities: Dict[str, float] = Field(
        default_factory=lambda: {"cx": 0.99, "u": 0.999, "measure": 0.95},
        description="Gate fidelities per type"
    )
    measurement_errors: Optional[List[float]] = Field(
        default=None,
        description="Meetfouten per qubit"
    )
    
    if PYDANTIC_AVAILABLE:
        @validator('n_qubits')
        def validate_qubits(cls, v):
            """Waarschuw bij veel qubits"""
            if v > 30:
                logger.warning(f"{v} qubits - simulatie kan traag zijn (> 2^{v} toestanden)")
            return v
        
        @validator('backend_name')
        def validate_backend(cls, v, values):
            """Valideer backend naam"""
            use_real = values.get('use_real_hardware', False)
            if use_real and not v.startswith('ibmq_'):
                logger.warning(f"Real hardware backend '{v}' bestaat mogelijk niet")
            return v


# ====================================================================
# COMPLETE HARDWARE CONFIGURATIE (UITGEBREID)
# ====================================================================

class HardwareConfig(BaseModel):
    """
    Complete hardware configuratie voor alle backends - UITGEBREID.
    
    Attributes:
        version: Configuratie versie
        backend: Gekozen backend
        cpu: CPU-specifieke configuratie
        cuda: CUDA/GPU-specifieke configuratie
        fpga: FPGA-specifieke configuratie
        quantum: Quantum-specifieke configuratie
        fallback_to_cpu: Val terug naar CPU
        log_level: Log level
        profile: Profileer hardware performance
        metrics_tracking: Track metrics
        metrics_interval: Metrics interval
        auto_detect: Auto-detect hardware
        preferred_order: Voorkeursvolgorde voor auto-detect
        validation_hooks: Validatie hooks
        created_at: Aanmaak timestamp
        updated_at: Laatste update timestamp
    """
    version: str = Field(
        default=ConfigVersion.CURRENT_VERSION,
        description="Configuratie versie"
    )
    backend: str = Field(
        default="auto",
        description="Gekozen backend",
        pattern="^(auto|cpu|cuda|fpga|quantum)$"
    )
    cpu: CPUConfig = Field(
        default_factory=CPUConfig,
        description="CPU-specifieke configuratie"
    )
    cuda: CUDAConfig = Field(
        default_factory=CUDAConfig,
        description="CUDA/GPU-specifieke configuratie"
    )
    fpga: FPGAConfig = Field(
        default_factory=FPGAConfig,
        description="FPGA-specifieke configuratie"
    )
    quantum: QuantumConfig = Field(
        default_factory=QuantumConfig,
        description="Quantum-specifieke configuratie"
    )
    fallback_to_cpu: bool = Field(
        default=True,
        description="Val terug naar CPU bij hardware fouten"
    )
    log_level: str = Field(
        default="INFO",
        description="Log level voor hardware operaties",
        pattern="^(DEBUG|INFO|WARNING|ERROR)$"
    )
    profile: bool = Field(
        default=False,
        description="Profileer hardware performance"
    )
    metrics_tracking: bool = Field(
        default=True,
        description="Track metrics"
    )
    metrics_interval: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Metrics interval in seconden"
    )
    auto_detect: bool = Field(
        default=True,
        description="Auto-detect hardware"
    )
    preferred_order: List[str] = Field(
        default=["fpga", "quantum", "cuda", "cpu"],
        description="Voorkeursvolgorde voor auto-detect"
    )
    validation_hooks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Validatie hooks"
    )
    created_at: Optional[float] = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Aanmaak timestamp"
    )
    updated_at: Optional[float] = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Laatste update timestamp"
    )
    
    if PYDANTIC_AVAILABLE:
        @validator('backend')
        def validate_backend(cls, v):
            """Valideer backend keuze"""
            valid_backends = ['auto', 'cpu', 'cuda', 'fpga', 'quantum']
            if v not in valid_backends:
                raise ValueError(f"Backend moet één van {valid_backends} zijn, niet {v}")
            return v
        
        @validator('preferred_order')
        def validate_preferred_order(cls, v):
            """Valideer voorkeursvolgorde"""
            valid_backends = {'cpu', 'cuda', 'fpga', 'quantum'}
            for backend in v:
                if backend not in valid_backends:
                    raise ValueError(f"Onbekende backend in preferred_order: {backend}")
            return v
    
    def get_backend_config(self, backend_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Haal configuratie op voor specifieke backend.
        
        Args:
            backend_name: Naam van backend ('cpu', 'cuda', etc.)
                        Als None, gebruik self.backend
        
        Returns:
            Dictionary met backend-specifieke configuratie
        """
        if backend_name is None:
            backend_name = self.backend
        
        if backend_name == 'auto':
            # Voor auto-detectie, geef alle configuraties terug
            return {
                'cpu': self._to_dict(self.cpu),
                'cuda': self._to_dict(self.cuda),
                'fpga': self._to_dict(self.fpga),
                'quantum': self._to_dict(self.quantum),
                'fallback_to_cpu': self.fallback_to_cpu,
                'log_level': self.log_level,
                'profile': self.profile,
                'preferred_order': self.preferred_order
            }
        
        config_map = {
            'cpu': self.cpu,
            'cuda': self.cuda,
            'fpga': self.fpga,
            'quantum': self.quantum
        }
        
        if backend_name in config_map:
            return self._to_dict(config_map[backend_name])
        else:
            logger.error(f"Onbekende backend: {backend_name}")
            return {}
    
    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        """Converteer object naar dictionary."""
        if hasattr(obj, 'dict'):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer complete configuratie naar dictionary."""
        result = {
            'version': self.version,
            'backend': self.backend,
            'cpu': self._to_dict(self.cpu),
            'cuda': self._to_dict(self.cuda),
            'fpga': self._to_dict(self.fpga),
            'quantum': self._to_dict(self.quantum),
            'fallback_to_cpu': self.fallback_to_cpu,
            'log_level': self.log_level,
            'profile': self.profile,
            'metrics_tracking': self.metrics_tracking,
            'metrics_interval': self.metrics_interval,
            'auto_detect': self.auto_detect,
            'preferred_order': self.preferred_order,
            'validation_hooks': self.validation_hooks,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # Update timestamp
        self.updated_at = datetime.now().timestamp()
        
        return result
    
    def to_yaml(self) -> str:
        """Exporteer als YAML."""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    def to_json(self, **kwargs) -> str:
        """Exporteer als JSON."""
        return json.dumps(self.to_dict(), **kwargs)
    
    def save(self, filepath: str):
        """Sla configuratie op in bestand."""
        ext = Path(filepath).suffix.lower()
        
        if ext in ['.yaml', '.yml']:
            with open(filepath, 'w') as f:
                yaml.dump(self.to_dict(), f)
        elif ext == '.json':
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        else:
            raise ValueError(f"Onbekend bestandstype: {ext}")
        
        logger.info(f"✅ Configuratie opgeslagen: {filepath}")
    
    def validate_all(self) -> List[str]:
        """Voer alle validatie hooks uit."""
        warnings = []
        
        # Check preferred order bevat alle backends
        if self.auto_detect:
            missing = {'cpu', 'cuda', 'fpga', 'quantum'} - set(self.preferred_order)
            if missing:
                warnings.append(f"Backends niet in preferred_order: {missing}")
        
        # Check log level
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            warnings.append(f"Ongeldig log level: {self.log_level}")
        
        # Run custom validation hooks
        for hook in self.validation_hooks:
            try:
                hook_name = hook.get('name', 'unknown')
                hook_func = hook.get('function')
                if hook_func and callable(hook_func):
                    result = hook_func(self)
                    if result:
                        warnings.append(f"Hook {hook_name}: {result}")
            except Exception as e:
                warnings.append(f"Fout in validation hook: {e}")
        
        return warnings


# ====================================================================
# CONFIGURATIE LADER (UITGEBREID)
# ====================================================================

def load_hardware_config(config_path: Optional[str] = None,
                        auto_migrate: bool = True) -> HardwareConfig:
    """
    Laad hardware configuratie vanuit bestand of gebruik standaard.
    
    Args:
        config_path: Pad naar YAML/JSON configuratie bestand
        auto_migrate: Automatisch migreren naar huidige versie
    
    Returns:
        HardwareConfig object
    """
    config = HardwareConfig()
    
    if config_path and os.path.exists(config_path):
        try:
            ext = Path(config_path).suffix.lower()
            
            if ext in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    config_dict = yaml.safe_load(f)
            elif ext == '.json':
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
            else:
                logger.error(f"Onbekend bestandstype: {ext}")
                return config
            
            # Extract hardware sectie
            hw_dict = config_dict.get('hardware', config_dict)
            
            # Check versie en migreer indien nodig
            version = hw_dict.get('version', '1.0')
            if auto_migrate and version != ConfigVersion.CURRENT_VERSION:
                if version in ConfigVersion.SUPPORTED_VERSIONS:
                    hw_dict = ConfigVersion.migrate(hw_dict, version)
                else:
                    logger.warning(f"Config versie {version} niet ondersteund, gebruik standaard")
                    return config
            
            if PYDANTIC_AVAILABLE:
                config = HardwareConfig(**hw_dict)
            else:
                # Handmatige constructie
                for key, value in hw_dict.items():
                    if hasattr(config, key):
                        if isinstance(value, dict) and key in ['cpu', 'cuda', 'fpga', 'quantum']:
                            sub_config = getattr(config, key)
                            for sub_key, sub_value in value.items():
                                if hasattr(sub_config, sub_key):
                                    setattr(sub_config, sub_key, sub_value)
                        else:
                            setattr(config, key, value)
            
            logger.info(f"📋 Configuratie geladen uit: {config_path}")
            logger.info(f"   Versie: {config.version}")
            
        except Exception as e:
            logger.error(f"Fout bij laden configuratie: {e}")
            logger.info("Gebruik standaard hardware configuratie")
    
    return config


# ====================================================================
# CONFIGURATIE SAMENVOEGEN
# ====================================================================

def merge_configs(base: HardwareConfig, 
                  override: Dict[str, Any],
                  strategy: str = 'deep') -> HardwareConfig:
    """
    Voeg twee configuraties samen.
    
    Args:
        base: Basis configuratie
        override: Override waarden
        strategy: 'shallow' of 'deep' merge
    
    Returns:
        Nieuwe samengevoegde configuratie
    """
    base_dict = base.to_dict()
    
    if strategy == 'shallow':
        base_dict.update(override)
    else:
        # Deep merge
        for key, value in override.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                base_dict[key].update(value)
            else:
                base_dict[key] = value
    
    if PYDANTIC_AVAILABLE:
        return HardwareConfig(**base_dict)
    else:
        new_config = HardwareConfig()
        for key, value in base_dict.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
        return new_config


# ====================================================================
# STANDAARD CONFIGURATIE (UITGEBREID)
# ====================================================================

DEFAULT_CONFIG = {
    'version': ConfigVersion.CURRENT_VERSION,
    'backend': 'auto',
    'cpu': {
        'precision': 'float64',
        'simulate_analog': True,
        'num_threads': 4,
        'use_blas': True,
        'cpu_affinity': None,
        'use_avx': True,
        'use_sse': True,
        'vector_size': 256,
        'cache_size': None
    },
    'cuda': {
        'device_id': 0,
        'memory_fraction': 0.8,
        'use_tensor_cores': True,
        'cudnn_benchmark': True,
        'allow_growth': False,
        'mixed_precision': False,
        'use_multi_gpu': False,
        'device_ids': [0],
        'sync_mode': 'async',
        'max_split_size': None
    },
    'fpga': {
        'bitstream': 'apeiron.bit',
        'timeout': 1.0,
        'use_interrupts': True,
        'dma_channels': 4,
        'clock_frequency': None,
        'use_dual_port': True,
        'parallel_fields': 16,
        'monitor_temperature': True,
        'max_temperature': 85.0,
        'power_saving': False,
        'max_power_watts': None,
        'bitstream_version': '1.0',
        'fpga_family': 'Kintex'
    },
    'quantum': {
        'n_qubits': 20,
        'shots': 1000,
        'use_real_hardware': False,
        'backend_name': 'aer_simulator',
        'optimization_level': 1,
        'noise_model': True,
        'coupling_map': False,
        'initial_layout': None,
        'use_entanglement': True,
        'max_circuit_depth': 100,
        'error_mitigation': 'zero_noise_extrapolation',
        'min_quantum_volume': 8,
        'shots_distribution': {'baseline': 0.5, 'mitigated': 0.5},
        'gate_fidelities': {'cx': 0.99, 'u': 0.999, 'measure': 0.95},
        'measurement_errors': None
    },
    'fallback_to_cpu': True,
    'log_level': 'INFO',
    'profile': False,
    'metrics_tracking': True,
    'metrics_interval': 60,
    'auto_detect': True,
    'preferred_order': ['fpga', 'quantum', 'cuda', 'cpu'],
    'validation_hooks': [],
    'created_at': None,
    'updated_at': None
}


# ====================================================================
# TEST & DEMONSTRATIE (UITGEBREID)
# ====================================================================

def demo():
    """Demonstreer hardware configuratie"""
    print("\n" + "="*80)
    print("🔧 HARDWARE CONFIGURATIE DEMONSTRATIE (UITGEBREID)")
    print("="*80)
    
    # Standaard configuratie
    print("\n📋 Standaard configuratie:")
    config = HardwareConfig()
    for key, value in config.to_dict().items():
        if key not in ['cpu', 'cuda', 'fpga', 'quantum', 'validation_hooks']:
            print(f"   {key}: {value}")
    
    # CPU config details
    print("\n💻 CPU configuratie (uitgebreid):")
    cpu_dict = config._to_dict(config.cpu)
    for key, value in cpu_dict.items():
        print(f"   {key}: {value}")
    
    # CUDA config details
    print("\n🎮 CUDA configuratie (uitgebreid):")
    cuda_dict = config._to_dict(config.cuda)
    for key, value in cuda_dict.items():
        print(f"   {key}: {value}")
    
    # FPGA config details
    print("\n⚡ FPGA configuratie (uitgebreid):")
    fpga_dict = config._to_dict(config.fpga)
    for key, value in fpga_dict.items():
        print(f"   {key}: {value}")
    
    # Quantum config details
    print("\n🌀 Quantum configuratie (uitgebreid):")
    quantum_dict = config._to_dict(config.quantum)
    for key, value in quantum_dict.items():
        print(f"   {key}: {value}")
    
    # Test get_backend_config
    print("\n🎯 Backend config voor 'cuda':")
    cuda_config = config.get_backend_config('cuda')
    for key, value in cuda_config.items():
        print(f"   {key}: {value}")
    
    # Test validatie
    print("\n✅ Validatie resultaten:")
    warnings = config.validate_all()
    for warning in warnings:
        print(f"   ⚠️ {warning}")
    if not warnings:
        print("   ✓ Geen waarschuwingen")
    
    # Test export
    print("\n📄 YAML export (eerste 10 regels):")
    yaml_str = config.to_yaml()
    for line in yaml_str.split('\n')[:10]:
        print(f"   {line}")
    print("   ...")
    
    print("\n" + "="*80)
    print(f"✅ Pydantic beschikbaar: {PYDANTIC_AVAILABLE}")
    print(f"✅ Config versie: {config.version}")
    print("="*80)


if __name__ == "__main__":
    demo()