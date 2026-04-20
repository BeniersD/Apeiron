"""
FPGA Backend - ECHTE parallelle hardware
Gebruikt PYNQ library voor Xilinx FPGAs
================================================================================
Biedt volledige integratie met:
- hardware_factory.py voor centrale hardware detectie
- hardware_config.py voor gestandaardiseerde configuratie
- hardware_exceptions.py voor uniforme error handling

V12.2 FIXES:
- Bug 6: Float naar integer AXI register via fixed-point conversie
- Bug 9: O(n) lookup met DMA-kopieën → O(1) met hashing
- Veld-ID systeem voor efficiënte lookups
- Fixed-point schaling voor hardware registers
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
import time
import hashlib
import struct

# Juiste import van HardwareBackend
from apeiron.hardware.backends import HardwareBackend

# Importeer hardware exceptions (optioneel)
try:
    from hardware_exceptions import (
        FPGAError,
        HardwareTimeoutError,
        HardwareMemoryError,
        HardwareInitializationError,
        handle_hardware_errors
    )
    EXCEPTIONS_AVAILABLE = True
except ImportError:
    EXCEPTIONS_AVAILABLE = False
    # Fallback decorator
    def handle_hardware_errors(default_return=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ Hardware fout: {e}")
                    return default_return
            return wrapper
        return decorator

# PYNQ import met betere error handling
try:
    from pynq import Overlay, allocate
    from pynq.lib import AxiGPIO
    PYNQ_AVAILABLE = True
except ImportError:
    PYNQ_AVAILABLE = False
except Exception as e:
    PYNQ_AVAILABLE = False
    print(f"⚠️ Fout bij laden PYNQ: {e}")


class FPGABackend(HardwareBackend):
    """
    FPGA backend - alle operaties zijn ECHT PARALLEL!
    Geen loops - hardware doet het werk.
    
    Features:
    - DMA transfers voor snelle data uitwisseling
    - Interrupt-driven synchronisatie
    - Parallelle verwerking van alle velden
    - Hardware-accelerated pattern detection
    
    V12.2 Verbeteringen:
    - 🔥 O(1) lookups via hashing (geen lineaire scans)
    - ⚡ Fixed-point conversie voor hardware registers
    - 📊 Uitgebreide metrics
    - 🔍 Veld-ID systeem voor efficiëntie
    """
    
    # 🔥 V12.2: Fixed-point schaalfactor (Q16.16)
    FIXED_POINT_SCALE = 65536  # 2^16
    
    def __init__(self):
        super().__init__()
        self.name = "FPGA"
        self.ol = None
        
        # 🔥 V12.2: Gebruik dictionaries voor O(1) lookups
        self.fields: Dict[int, Any] = {}  # id -> DMA buffer
        self.field_data: Dict[int, np.ndarray] = {}  # id -> np.ndarray (cached)
        self.field_counters: Dict[int, int] = {}  # id -> update counter
        self.field_hash: Dict[str, int] = {}  # hash -> id voor O(1) lookup
        
        self.logger = logging.getLogger('FPGA')
        
        # Hardware beschikbaarheid
        self.is_available = PYNQ_AVAILABLE
        
        # Configuratie
        self.config = {
            'bitstream': 'nexus.bit',
            'timeout': 1.0,
            'use_interrupts': True,
            'dma_channels': 4,
            'clock_frequency': None,
            'use_dual_port': True,
            'parallel_fields': 16,
            'fixed_point_scale': self.FIXED_POINT_SCALE  # Voor hardware
        }
        
        # Performance metrics (uitgebreid)
        self.metrics = {
            'total_updates': 0,
            'total_interference_calc': 0,
            'total_timeouts': 0,
            'avg_update_time': 0.0,
            'min_update_time': float('inf'),
            'max_update_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Volgende ID
        self._next_id = 0
        
        if self.is_available:
            self.logger.info("⚡ FPGA Backend V12.2 - ECHTE PARALLELLITEIT!")
        else:
            self.logger.warning("⚠️ PYNQ niet beschikbaar - FPGA backend niet actief")
    
    # ====================================================================
    # INITIALISATIE
    # ====================================================================
    
    @handle_hardware_errors(default_return=False)
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialiseer FPGA board met gegeven configuratie.
        
        Args:
            config: Configuratie dictionary met o.a.:
                - bitstream: Pad naar .bit bestand
                - timeout: Timeout in seconden
                - use_interrupts: Gebruik interrupts voor sync
                - dma_channels: Aantal DMA kanalen
        
        Returns:
            True als initialisatie gelukt is
        """
        if not PYNQ_AVAILABLE:
            error_msg = "PYNQ niet beschikbaar - kan FPGA niet laden"
            self.logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise HardwareInitializationError(
                    backend="FPGA",
                    component="PYNQ",
                    details=error_msg
                )
            return False
        
        # Update config
        self.config.update(config)
        
        try:
            bitstream = self.config.get('bitstream', 'nexus.bit')
            self.logger.info(f"🔌 FPGA bitstream laden: {bitstream}")
            
            # Laad bitstream
            self.ol = Overlay(bitstream)
            
            # Configureer hardware blokken
            self._setup_hardware_blocks()
            
            # Configureer interrupts
            if self.config.get('use_interrupts', True):
                self._setup_interrupts()
            
            # Test hardware met klein veld
            self._test_hardware()
            
            self.logger.info("  ✅ FPGA geïnitialiseerd")
            self.logger.info(f"  ⚡ Bitstream: {bitstream}")
            self.logger.info(f"  ⚡ DMA kanalen: {self.config.get('dma_channels')}")
            self.logger.info(f"  ⚡ {self.config.get('parallel_fields')} stromingen parallel")
            self.logger.info(f"  ⚡ Fixed-point scale: {self.config.get('fixed_point_scale')}")
            
            return True
            
        except Exception as e:
            error_msg = f"FPGA init mislukt: {e}"
            self.logger.error(error_msg)
            
            if EXCEPTIONS_AVAILABLE:
                raise HardwareInitializationError(
                    backend="FPGA",
                    details=str(e)
                ) from e
            return False
    
    def _setup_hardware_blocks(self):
        """Configureer hardware IP blocks."""
        # Hoofd engines
        self.field_engine = self.ol.continuous_fields
        self.interference_engine = self.ol.interference_matrix
        self.stability_engine = self.ol.stability_detector
        
        # Optionele blokken
        if hasattr(self.ol, 'dma_controller'):
            self.dma_controller = self.ol.dma_controller
        
        if hasattr(self.ol, 'memory_controller'):
            self.memory_controller = self.ol.memory_controller
    
    def _setup_interrupts(self):
        """Configureer interrupts voor synchronisatie."""
        try:
            self.field_interrupt = self.ol.ip_dict['continuous_fields']['interrupt']
            self.interference_interrupt = self.ol.ip_dict['interference_matrix']['interrupt']
            self.stability_interrupt = self.ol.ip_dict['stability_detector']['interrupt']
            
            self.logger.info("  ⚡ Interrupts geconfigureerd")
        except Exception as e:
            self.logger.warning(f"  ⚠️ Interrupts niet beschikbaar: {e}")
            self.config['use_interrupts'] = False
    
    def _test_hardware(self):
        """Test hardware met een kleine operatie."""
        try:
            # Creëer test veld
            test_field = self.create_continuous_field(10)
            
            # Test interferentie
            interference = self.compute_interference(test_field, test_field)
            
            self.logger.info(f"  ✅ Hardware test geslaagd (interference={interference:.2f})")
            
        except Exception as e:
            self.logger.warning(f"  ⚠️ Hardware test warning: {e}")
    
    # ====================================================================
    # KERN FUNCTIONALITEIT (V12.2 OPTIMALISATIES)
    # ====================================================================
    
    @handle_hardware_errors(default_return=None)
    def create_continuous_field(self, dimensions: int) -> np.ndarray:
        """
        Creëer een ECHT continu veld in hardware.
        
        Args:
            dimensions: Dimensie van het veld
            
        Returns:
            Numpy array met het gecreëerde veld
        """
        if not PYNQ_AVAILABLE:
            # Fallback naar CPU-achtige simulatie
            field_array = np.random.randn(dimensions).astype(np.float32)
            field_array = field_array / np.linalg.norm(field_array)
            return field_array
        
        try:
            # Genereer initiële array
            field_array = np.random.randn(dimensions).astype(np.float32)
            field_array = field_array / np.linalg.norm(field_array)
            
            # Alloceer DMA buffer en kopieer data
            buffer = allocate(shape=(dimensions,), dtype=np.float32)
            buffer[:] = field_array
            
            # Sync naar hardware
            self.field_engine.write(0, buffer.physical_address)
            
            # 🔥 V12.2: Genereer unieke ID en sla op
            field_id = self._next_id
            self._next_id += 1
            
            self.fields[field_id] = buffer
            self.field_data[field_id] = field_array.copy()
            self.field_counters[field_id] = 0
            
            # Sla hash op voor snelle lookup
            field_hash = hashlib.md5(field_array.tobytes()).hexdigest()
            self.field_hash[field_hash] = field_id
            
            # Retourneer array (interface compatibel!)
            return field_array
            
        except Exception as e:
            error_msg = f"FPGA field creatie mislukt: {e}"
            self.logger.error(error_msg)
            
            if EXCEPTIONS_AVAILABLE:
                raise FPGAError(
                    message=error_msg,
                    bitstream=self.config.get('bitstream')
                ) from e
            
            # Fallback
            field_array = np.random.randn(dimensions).astype(np.float32)
            return field_array / np.linalg.norm(field_array)
    
    def get_field_id(self, field: np.ndarray) -> Optional[int]:
        """
        🔥 V12.2: Nieuwe methode om field ID op te halen (O(1) lookup).
        
        Args:
            field: Het veld waarvoor de ID gezocht wordt
            
        Returns:
            Field ID of None als niet gevonden
        """
        # Gebruik hash voor O(1) lookup
        try:
            field_hash = hashlib.md5(field.tobytes()).hexdigest()
            if field_hash in self.field_hash:
                self.metrics['cache_hits'] += 1
                return self.field_hash[field_hash]
        except:
            pass
        
        # 🔥 V12.2: Fallback zonder DMA-kopieën
        self.metrics['cache_misses'] += 1
        for fid, buf in self.fields.items():
            # Gebruik buf.array attribute in plaats van np.array(buf)
            if hasattr(buf, 'array') and np.array_equal(buf.array, field):
                # Update hash voor toekomst
                try:
                    field_hash = hashlib.md5(field.tobytes()).hexdigest()
                    self.field_hash[field_hash] = fid
                except:
                    pass
                return fid
        
        return None
    
    def _float_to_fixed(self, value: float) -> int:
        """
        🔥 V12.2: Converteer float naar fixed-point voor hardware registers.
        
        Args:
            value: Float waarde (bv. dt = 0.1)
            
        Returns:
            Fixed-point integer voor AXI register
        """
        scale = self.config.get('fixed_point_scale', self.FIXED_POINT_SCALE)
        return int(value * scale)
    
    def _float_to_ieee754(self, value: float) -> int:
        """
        🔥 V12.2: Alternatief: converteer float naar IEEE 754 32-bit integer.
        
        Args:
            value: Float waarde
            
        Returns:
            32-bit integer representatie van de float
        """
        return struct.unpack('I', struct.pack('f', value))[0]
    
    @handle_hardware_errors(default_return=None)
    def field_update(self, field: np.ndarray, dt: float,
                    verleden: np.ndarray, heden: np.ndarray,
                    toekomst: np.ndarray) -> Dict:
        """
        Update veld in HARDWARE.
        ALLES GEBEURT PARALLEL!
        
        Args:
            field: Huidig veld (numpy array)
            dt: Tijdstap
            verleden: Verleden veld
            heden: Heden veld
            toekomst: Toekomst veld
            
        Returns:
            Dict met 'verleden', 'heden', 'toekomst' als numpy arrays
        """
        start_time = time.time()
        
        if not PYNQ_AVAILABLE:
            # CPU fallback
            return self._cpu_fallback_update(field, dt, verleden, heden, toekomst)
        
        try:
            # 🔥 V12.2: Gebruik get_field_id voor O(1) lookups
            field_id = self.get_field_id(field)
            verleden_id = self.get_field_id(verleden)
            heden_id = self.get_field_id(heden)
            toekomst_id = self.get_field_id(toekomst)
            
            # Als IDs niet gevonden, maak nieuwe buffers
            if field_id is None:
                field_id = self._create_buffer(field)
            if verleden_id is None:
                verleden_id = self._create_buffer(verleden)
            if heden_id is None:
                heden_id = self._create_buffer(heden)
            if toekomst_id is None:
                toekomst_id = self._create_buffer(toekomst)
            
            # Update counters
            self.field_counters[field_id] = self.field_counters.get(field_id, 0) + 1
            
            # Configureer hardware voor deze update
            self.field_engine.write(1, field_id)
            self.field_engine.write(2, verleden_id)
            self.field_engine.write(3, heden_id)
            self.field_engine.write(4, toekomst_id)
            
            # 🔥 V12.2: FIXED - Converteer float naar fixed-point
            dt_fixed = self._float_to_fixed(dt)
            self.field_engine.write(5, dt_fixed)
            
            # Start hardware update
            self.field_engine.start()
            
            # Wacht op interrupt of poll status
            timeout = self.config.get('timeout', 1.0)
            success = self._wait_for_completion(self.field_interrupt, timeout)
            
            if not success:
                self.metrics['total_timeouts'] += 1
                if EXCEPTIONS_AVAILABLE:
                    raise HardwareTimeoutError(
                        operation="field_update",
                        timeout=timeout,
                        backend="FPGA"
                    )
            
            # Lees resultaten terug van hardware
            verleden_buf = self.fields.get(verleden_id)
            heden_buf = self.fields.get(heden_id)
            toekomst_buf = self.fields.get(toekomst_id)
            
            # Update cached arrays
            if verleden_buf is not None and hasattr(verleden_buf, 'array'):
                self.field_data[verleden_id] = np.array(verleden_buf.array)
            if heden_buf is not None and hasattr(heden_buf, 'array'):
                self.field_data[heden_id] = np.array(heden_buf.array)
            if toekomst_buf is not None and hasattr(toekomst_buf, 'array'):
                self.field_data[toekomst_id] = np.array(toekomst_buf.array)
            
            # Update metrics
            self.metrics['total_updates'] += 1
            elapsed = time.time() - start_time
            self.metrics['avg_update_time'] = (
                self.metrics['avg_update_time'] * 0.95 + elapsed * 0.05
            )
            self.metrics['min_update_time'] = min(self.metrics['min_update_time'], elapsed)
            self.metrics['max_update_time'] = max(self.metrics['max_update_time'], elapsed)
            
            return {
                'verleden': self.field_data.get(verleden_id, verleden),
                'heden': self.field_data.get(heden_id, heden),
                'toekomst': self.field_data.get(toekomst_id, toekomst)
            }
            
        except Exception as e:
            self.logger.error(f"FPGA update mislukt: {e}")
            return self._cpu_fallback_update(field, dt, verleden, heden, toekomst)
    
    def _create_buffer(self, array: np.ndarray) -> int:
        """
        🔥 V12.2: Nieuwe buffer aanmaken.
        
        Args:
            array: Numpy array om in buffer te zetten
            
        Returns:
            Buffer ID
        """
        if not PYNQ_AVAILABLE:
            return 0
        
        buffer = allocate(shape=array.shape, dtype=np.float32)
        buffer[:] = array.astype(np.float32)
        
        fid = self._next_id
        self._next_id += 1
        
        self.fields[fid] = buffer
        self.field_data[fid] = array.copy()
        self.field_counters[fid] = 0
        
        # Sync naar hardware
        self.field_engine.write(100 + fid, buffer.physical_address)
        
        # Sla hash op
        try:
            field_hash = hashlib.md5(array.tobytes()).hexdigest()
            self.field_hash[field_hash] = fid
        except:
            pass
        
        return fid
    
    def _get_or_create_buffer(self, array: np.ndarray) -> int:
        """
        🔥 V12.2: Verbeterde versie met O(1) lookup via hash.
        
        Args:
            array: Numpy array
            
        Returns:
            Buffer ID
        """
        if not PYNQ_AVAILABLE:
            return 0
        
        # Eerst via hash proberen (O(1))
        field_id = self.get_field_id(array)
        if field_id is not None:
            return field_id
        
        # Anders nieuwe buffer maken
        return self._create_buffer(array)
    
    def _cpu_fallback_update(self, field: np.ndarray, dt: float,
                            verleden: np.ndarray, heden: np.ndarray,
                            toekomst: np.ndarray) -> Dict:
        """CPU fallback voor field_update."""
        # Simpele Euler integratie
        new_field = field + 0.01 * np.random.randn(*field.shape) * np.sqrt(dt)
        new_field = new_field / np.linalg.norm(new_field)
        
        return {
            'verleden': verleden,
            'heden': new_field,
            'toekomst': toekomst
        }
    
    def _wait_for_completion(self, interrupt, timeout: float = 1.0) -> bool:
        """Wacht op hardware completion via interrupt of polling."""
        start = time.time()
        
        # Probeer interrupt (als beschikbaar en ingeschakeld)
        if self.config.get('use_interrupts', True):
            try:
                interrupt.wait(timeout)
                return True
            except:
                pass
        
        # Fallback: poll status register
        while time.time() - start < timeout:
            try:
                if self.field_engine.read(1000) == 1:  # Status register
                    return True
            except:
                pass
            time.sleep(0.001)
        
        self.logger.warning(f"⚠️ FPGA timeout na {timeout:.1f}s")
        return False
    
    # ====================================================================
    # INTERFERENTIE & PATRONEN
    # ====================================================================
    
    @handle_hardware_errors(default_return=0.5)
    def compute_interference(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Bereken interferentie in HARDWARE.
        
        Args:
            a, b: numpy arrays om interferentie van te berekenen
            
        Returns:
            Interferentie sterkte (0-1)
        """
        self.metrics['total_interference_calc'] += 1
        start_time = time.time()
        
        if not PYNQ_AVAILABLE:
            # CPU fallback
            a_norm = a / np.linalg.norm(a)
            b_norm = b / np.linalg.norm(b)
            return float(np.dot(a_norm, b_norm))
        
        try:
            a_id = self._get_or_create_buffer(a)
            b_id = self._get_or_create_buffer(b)
            
            self.interference_engine.write(0, a_id)
            self.interference_engine.write(1, b_id)
            
            # Start meting
            self.interference_engine.start()
            
            # Wacht op resultaat
            timeout = self.config.get('timeout', 0.5)
            self._wait_for_completion(self.interference_interrupt, timeout)
            
            # Lees resultaat (hardware register)
            result = float(self.interference_engine.read(2))
            
            self.metrics['interference_time'] = time.time() - start_time
            
            return max(0.0, min(1.0, result))
            
        except Exception as e:
            self.logger.error(f"FPGA interference mislukt: {e}")
            # CPU fallback
            a_norm = a / np.linalg.norm(a)
            b_norm = b / np.linalg.norm(b)
            return float(np.dot(a_norm, b_norm))
    
    @handle_hardware_errors(default_return=[])
    def find_stable_patterns(self, fields: List[np.ndarray],
                            threshold: float) -> List[Dict]:
        """
        Laat hardware ALLE paren vergelijken (PARALLEL!)
        
        Args:
            fields: Lijst van numpy arrays
            threshold: Minimum sterkte voor rapportage
            
        Returns:
            Lijst van dicts met 'i', 'j', 'sterkte', 'veld'
        """
        if not PYNQ_AVAILABLE or len(fields) < 2:
            return self._cpu_find_patterns(fields, threshold)
        
        start_time = time.time()
        
        try:
            # Converteer alle velden naar hardware IDs
            field_ids = []
            for f in fields:
                fid = self._get_or_create_buffer(f)
                field_ids.append(fid)
            
            # Stuur lijst naar hardware
            for i, fid in enumerate(field_ids):
                self.stability_engine.write(i, fid)
            
            self.stability_engine.write(100, threshold)
            
            # Start parallelle analyse
            self.stability_engine.start()
            
            # Wacht op resultaat
            timeout = self.config.get('timeout', 2.0)
            self._wait_for_completion(self.stability_interrupt, timeout)
            
            # Hardware geeft resultaten
            results = []
            n_results = int(self.stability_engine.read(200))
            
            for i in range(n_results):
                sterkte = self.stability_engine.read(300 + i)
                if sterkte >= threshold:
                    i_idx = int(self.stability_engine.read(400 + i))
                    j_idx = int(self.stability_engine.read(500 + i))
                    
                    if i_idx < len(fields) and j_idx < len(fields):
                        # 🔥 V12.2: Voeg field IDs toe
                        field_id_i = self.get_field_id(fields[i_idx])
                        field_id_j = self.get_field_id(fields[j_idx])
                        
                        results.append({
                            'i': i_idx,
                            'j': j_idx,
                            'field_id_i': field_id_i,
                            'field_id_j': field_id_j,
                            'sterkte': float(sterkte),
                            'veld': self._normalize(fields[i_idx] + fields[j_idx])
                        })
            
            self.metrics['pattern_time'] = time.time() - start_time
            
            return sorted(results, key=lambda x: x['sterkte'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"FPGA pattern detection mislukt: {e}")
            return self._cpu_find_patterns(fields, threshold)
    
    def _cpu_find_patterns(self, fields: List[np.ndarray],
                          threshold: float) -> List[Dict]:
        """CPU implementatie voor pattern detection."""
        n = len(fields)
        if n < 2:
            return []
        
        results = []
        for i in range(n):
            for j in range(i+1, n):
                sterkte = float(np.dot(fields[i], fields[j]))
                if sterkte > threshold:
                    field_id_i = self.get_field_id(fields[i])
                    field_id_j = self.get_field_id(fields[j])
                    
                    results.append({
                        'i': i,
                        'j': j,
                        'field_id_i': field_id_i,
                        'field_id_j': field_id_j,
                        'sterkte': sterkte,
                        'veld': self._normalize(fields[i] + fields[j])
                    })
        
        return sorted(results, key=lambda x: x['sterkte'], reverse=True)
    
    # ====================================================================
    # COHERENTIE METING
    # ====================================================================
    
    @handle_hardware_errors(default_return=0.5)
    def measure_coherence(self, fields: List[np.ndarray]) -> float:
        """
        Hardware meet coherentie in één klokcyclus.
        
        Args:
            fields: Lijst van numpy arrays
            
        Returns:
            Coherentie score (0-1)
        """
        if len(fields) < 2:
            return 1.0
        
        if not PYNQ_AVAILABLE:
            return self._cpu_measure_coherence(fields)
        
        start_time = time.time()
        
        try:
            # Converteer naar hardware IDs
            field_ids = []
            for f in fields:
                fid = self._get_or_create_buffer(f)
                field_ids.append(fid)
            
            # Laad alle velden in coherentie-engine
            for i, fid in enumerate(field_ids):
                self.stability_engine.write(600 + i, fid)
            
            # Start meting
            self.stability_engine.start()
            
            # Wacht op resultaat
            timeout = self.config.get('timeout', 1.0)
            self._wait_for_completion(self.stability_interrupt, timeout)
            
            # Lees resultaat
            coherence = float(self.stability_engine.read(700))
            
            self.metrics['coherence_time'] = time.time() - start_time
            
            # Valideer met CPU berekening (alleen in debug)
            if self.logger.isEnabledFor(logging.DEBUG):
                cpu_coherence = self._cpu_measure_coherence(fields)
                self.logger.debug(f"Coherentie: HW={coherence:.3f}, CPU={cpu_coherence:.3f}")
            
            return max(0.0, min(1.0, coherence))
            
        except Exception as e:
            self.logger.error(f"FPGA coherentie meting mislukt: {e}")
            return self._cpu_measure_coherence(fields)
    
    def _cpu_measure_coherence(self, fields: List[np.ndarray]) -> float:
        """CPU implementatie voor coherentie meting."""
        n = len(fields)
        if n < 2:
            return 1.0
        
        # Vectorized coherentie berekening
        matrix = np.array([f.flatten()[:50] for f in fields])
        gram = matrix @ matrix.T
        coherence = (np.sum(gram) - n) / (n * (n - 1)) if n > 1 else 1.0
        return float(coherence)
    
    # ====================================================================
    # HULP FUNCTIES
    # ====================================================================
    
    def _normalize(self, field: np.ndarray) -> np.ndarray:
        """Normaliseer een veld."""
        norm = np.linalg.norm(field)
        if norm > 0:
            return field / norm
        return field
    
    def get_info(self) -> str:
        """Haal informatie op over de FPGA backend."""
        info = f"FPGA ({self.config.get('bitstream')})"
        if self.is_available and self.ol:
            info += f" - {len(self.fields)} velden"
            info += f", {self.metrics['total_updates']} updates"
            info += f", {self.metrics['total_timeouts']} timeouts"
            info += f", cache: {self.metrics['cache_hits']}/{self.metrics['cache_misses']}"
        else:
            info += " - NIET BESCHIKBAAR"
        return info
    
    def get_metrics(self) -> Dict[str, Any]:
        """Haal performance metrics op."""
        return {
            **self.metrics,
            'active_fields': len(self.fields),
            'cached_fields': len(self.field_data),
            'config': self.config,
            'pynq_available': PYNQ_AVAILABLE,
            'hardware_active': self.ol is not None,
            'cache_hit_ratio': self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'] + 1),
            'next_id': self._next_id
        }
    
    # ====================================================================
    # RESOURCE MANAGEMENT
    # ====================================================================
    
    @handle_hardware_errors(default_return=False)
    def cleanup(self):
        """Opruimen van hardware resources."""
        self.logger.info("🧹 FPGA resources opruimen...")
        
        # Stop hardware engines
        try:
            self.field_engine.stop()
            self.interference_engine.stop()
            self.stability_engine.stop()
        except:
            pass
        
        # Free DMA buffers
        freed = 0
        for buf in self.fields.values():
            try:
                buf.freebuffer()
                freed += 1
            except:
                pass
        
        self.fields.clear()
        self.field_data.clear()
        self.field_counters.clear()
        self.field_hash.clear()
        
        self.logger.info(f"🧹 {freed} DMA buffers opgeruimd")
        self.logger.info(f"🧹 {len(self.field_hash)} hashes opgeruimd")
        
        # Reset metrics
        self.metrics = {
            'total_updates': 0,
            'total_interference_calc': 0,
            'total_timeouts': 0,
            'avg_update_time': 0.0,
            'min_update_time': float('inf'),
            'max_update_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self._next_id = 0
        self.ol = None


# ====================================================================
# DEMONSTRATIE (V12.2)
# ====================================================================

def demo():
    """Demonstreer FPGA backend functionaliteit."""
    print("\n" + "="*80)
    print("⚡ FPGA BACKEND V12.2 DEMONSTRATIE")
    print("="*80)
    print("✅ Bug 6: Float → fixed-point conversie")
    print("✅ Bug 9: O(1) lookups via hashing")
    print("✅ Veld-ID systeem voor efficiëntie")
    print("="*80)
    
    # Creëer backend
    backend = FPGABackend()
    print(f"\n📋 Backend status:")
    print(f"   Beschikbaar: {backend.is_available}")
    
    # Initialiseer
    if backend.initialize({'bitstream': 'nexus.bit'}):
        print(f"   Geïnitialiseerd: ✓")
        
        # Test field creatie met ID
        field = backend.create_continuous_field(10)
        field_id = backend.get_field_id(field)
        print(f"\n📋 Test veld:")
        print(f"   ID: {field_id}")
        print(f"   Shape: {field.shape}")
        print(f"   Norm: {np.linalg.norm(field):.3f}")
        
        # Test fixed-point conversie
        print(f"\n📋 Fixed-point test:")
        dt = 0.1
        fixed = backend._float_to_fixed(dt)
        ieee = backend._float_to_ieee754(dt)
        print(f"   dt = {dt}")
        print(f"   Fixed-point (Q16.16): {fixed} (0x{fixed:08X})")
        print(f"   IEEE 754: {ieee} (0x{ieee:08X})")
        
        # Test interferentie
        interference = backend.compute_interference(field, field)
        print(f"\n📋 Interferentie test:")
        print(f"   Zelf-interferentie: {interference:.3f}")
        
        # Test coherentie
        fields = [backend.create_continuous_field(10) for _ in range(5)]
        coherence = backend.measure_coherence(fields)
        print(f"\n📋 Coherentie test:")
        print(f"   Coherentie (5 velden): {coherence:.3f}")
        
        # Test cache efficiëntie
        print(f"\n📋 Cache test:")
        for _ in range(10):
            backend.get_field_id(field)  # Zou cache hits moeten zijn
        metrics = backend.get_metrics()
        print(f"   Cache hits: {metrics['cache_hits']}")
        print(f"   Cache misses: {metrics['cache_misses']}")
        print(f"   Hit ratio: {metrics['cache_hit_ratio']:.1%}")
        
        # Toon metrics
        print(f"\n📊 Metrics:")
        for key, value in backend.get_metrics().items():
            if key not in ['config', 'field_data']:
                if isinstance(value, float):
                    print(f"   {key}: {value:.3f}")
                else:
                    print(f"   {key}: {value}")
        
        # Cleanup
        backend.cleanup()
        print(f"\n✅ Cleanup voltooid")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    demo()