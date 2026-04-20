"""
EVENT BUS – Enterprise‑grade Asynchrone Communicatie (Professional Edition)
===========================================================================
Volledige event bus met pluggable backends, persistentie, encryptie, compressie,
circuit breaker, retry, batch processing, event sourcing, schema registry,
routing, transformaties, dead letter queue en Prometheus metrics.

Kenmerken:
- Configuratie via dataclass
- Backends: Memory, Redis (Kafka voorbereid)
- Serialisatie: JSON, Pickle, MsgPack (optioneel)
- Persistentie: SQLite (aiosqlite) voor event store
- Event sourcing: complete log van alle events
- Encryptie: Fernet (cryptography)
- Compressie: zlib
- Circuit breaker per subscriber
- Retry policy met exponentiële backoff
- Batch processing
- Rate limiting (token bucket)
- Dead letter queue met herverwerking en replay
- Schema registry (optionele validatie)
- Event routing naar andere bussen
- Event transformaties (pre‑processing)
- Content‑based filtering
- Prometheus metrics
- Volledig async/await
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import pickle
import sqlite3
import time
import uuid
import zlib
from collections import defaultdict, deque
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    Union,
    runtime_checkable,
)

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONELE IMPORTS (lazy)
# ============================================================================
_import_cache: Dict[str, Any] = {}


def _lazy_import(module: str, name: str) -> Any:
    key = f"{module}.{name}"
    if key not in _import_cache:
        try:
            mod = __import__(module, fromlist=[name])
            _import_cache[key] = getattr(mod, name)
        except ImportError:
            _import_cache[key] = None
    return _import_cache[key]


def _is_redis_available() -> bool:
    return _lazy_import("redis.asyncio", "Redis") is not None


def _is_prometheus_available() -> bool:
    return _lazy_import("prometheus_client", "Counter") is not None


def _is_aiohttp_available() -> bool:
    return _lazy_import("aiohttp", "ClientSession") is not None


def _is_cryptography_available() -> bool:
    return _lazy_import("cryptography.fernet", "Fernet") is not None


def _is_msgpack_available() -> bool:
    return _lazy_import("msgpack", "packb") is not None


def _is_aiosqlite_available() -> bool:
    return _lazy_import("aiosqlite", "connect") is not None


# ============================================================================
# CONFIGURATIE
# ============================================================================


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    DROPPED = "dropped"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    backoff_factor: float = 2.0
    max_delay: float = 30.0
    retry_on: Tuple[Type[Exception], ...] = (Exception,)


@dataclass(frozen=True)
class CircuitBreakerConfig:
    failure_threshold: int = 5
    timeout: float = 60.0


@dataclass(frozen=True)
class EventBusConfig:
    """Volledige configuratie voor de event bus."""

    # Identificatie
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Core
    max_history: int = 10000
    max_queue_size: int = 10000
    batch_size: int = 10
    batch_timeout: float = 0.1
    rate_limit: Optional[float] = None

    # Persistentie (event store)
    enable_persistence: bool = False
    persistence_path: str = "events.db"

    # Event sourcing (aparte log)
    enable_event_sourcing: bool = False
    sourcing_path: str = "event_log.db"

    # Distributed backend
    enable_distributed: bool = False
    distributed_backend: str = "redis"  # redis, kafka
    redis_url: str = "redis://localhost:6379"

    # Serialisatie
    serializer: str = "json"  # json, pickle, msgpack

    # Encryptie
    enable_encryption: bool = False
    encryption_key: Optional[bytes] = None

    # Compressie
    enable_compression: bool = False
    compression_threshold: int = 1024

    # Retry & Circuit Breaker
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)

    # Metrics
    enable_prometheus: bool = False
    prometheus_port: Optional[int] = None

    # Schema Registry
    enable_schema_registry: bool = False

    # Dead letter queue
    dead_letter_max_size: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ============================================================================
# PROTOCOLLEN
# ============================================================================


@runtime_checkable
class EventBackend(Protocol):
    async def publish(self, channel: str, message: bytes) -> None: ...
    async def subscribe(self, channel: str) -> None: ...
    async def get_message(self, timeout: float = 1.0) -> Optional[Any]: ...
    async def close(self) -> None: ...


@runtime_checkable
class EventSerializer(Protocol):
    def serialize(self, event: "Event") -> bytes: ...
    def deserialize(self, data: bytes) -> "Event": ...


# ============================================================================
# SERIALIZERS
# ============================================================================


class JSONSerializer:
    def serialize(self, event: Event) -> bytes:
        data = {
            "id": event.id,
            "type": event.type,
            "data": event.data,
            "source": event.source,
            "priority": event.priority.value,
            "timestamp": event.timestamp,
            "ttl": event.ttl,
            "retry_count": event.retry_count,
            "status": event.status.value,
            "metadata": event.metadata,
        }
        return json.dumps(data).encode()

    def deserialize(self, data: bytes) -> Event:
        obj = json.loads(data)
        return Event(
            id=obj["id"],
            type=obj["type"],
            data=obj["data"],
            source=obj["source"],
            priority=EventPriority(obj["priority"]),
            timestamp=obj["timestamp"],
            ttl=obj["ttl"],
            retry_count=obj["retry_count"],
            status=EventStatus(obj["status"]),
            metadata=obj["metadata"],
        )


class PickleSerializer:
    def serialize(self, event: Event) -> bytes:
        return pickle.dumps(event)

    def deserialize(self, data: bytes) -> Event:
        return pickle.loads(data)


class MsgPackSerializer:
    def __init__(self):
        if not _is_msgpack_available():
            raise RuntimeError("msgpack niet beschikbaar")
        self._packb = _lazy_import("msgpack", "packb")
        self._unpackb = _lazy_import("msgpack", "unpackb")

    def serialize(self, event: Event) -> bytes:
        data = {
            "id": event.id,
            "type": event.type,
            "data": event.data,
            "source": event.source,
            "priority": event.priority.value,
            "timestamp": event.timestamp,
            "ttl": event.ttl,
            "retry_count": event.retry_count,
            "status": event.status.value,
            "metadata": event.metadata,
        }
        return self._packb(data)

    def deserialize(self, data: bytes) -> Event:
        obj = self._unpackb(data)
        return Event(
            id=obj["id"],
            type=obj["type"],
            data=obj["data"],
            source=obj["source"],
            priority=EventPriority(obj["priority"]),
            timestamp=obj["timestamp"],
            ttl=obj["ttl"],
            retry_count=obj["retry_count"],
            status=EventStatus(obj["status"]),
            metadata=obj["metadata"],
        )


# ============================================================================
# EVENT DATACLASS
# ============================================================================


@dataclass(slots=True)
class Event:
    id: str
    type: str
    data: Any
    source: str
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None
    retry_count: int = 0
    status: EventStatus = EventStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure: Optional[float] = None

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.config.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self) -> None:
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure = time.time()
        if self.failure_count >= self.config.failure_threshold and self.state == "CLOSED":
            self.state = "OPEN"
            logger.warning(f"🔌 Circuit breaker geopend na {self.failure_count} fouten")


# ============================================================================
# SUBSCRIPTION
# ============================================================================


@dataclass
class Subscription:
    callback: Callable[[Event], Awaitable[None]]
    priority: int = 0
    filter_func: Optional[Callable[[Event], bool]] = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    circuit_breaker: CircuitBreaker = field(default_factory=lambda: CircuitBreaker(CircuitBreakerConfig()))
    call_count: int = 0
    error_count: int = 0
    avg_duration: float = 0.0


# ============================================================================
# ENCRYPTIE / COMPRESSIE HULP
# ============================================================================


class DataTransformer:
    def __init__(self, config: EventBusConfig):
        self.config = config
        self._cipher = None
        if config.enable_encryption and _is_cryptography_available():
            fernet = _lazy_import("cryptography.fernet", "Fernet")
            key = config.encryption_key or fernet.generate_key()
            self._cipher = fernet(key)

    def encode(self, data: bytes) -> bytes:
        if self.config.enable_compression and len(data) > self.config.compression_threshold:
            data = zlib.compress(data)
        if self._cipher:
            data = self._cipher.encrypt(data)
        return data

    def decode(self, data: bytes) -> bytes:
        if self._cipher:
            data = self._cipher.decrypt(data)
        if self.config.enable_compression:
            try:
                data = zlib.decompress(data)
            except zlib.error:
                pass
        return data


# ============================================================================
# PERSISTENTIE (SQLite)
# ============================================================================


class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not _is_aiosqlite_available():
            raise RuntimeError("aiosqlite niet beschikbaar")
        aiosqlite = _lazy_import("aiosqlite", "connect")
        self._conn = await aiosqlite(self.db_path)
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT,
                data BLOB,
                source TEXT,
                priority INTEGER,
                timestamp REAL,
                ttl REAL,
                retry_count INTEGER,
                status TEXT,
                metadata TEXT
            )
            """
        )
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)"
        )
        await self._conn.commit()

    async def save(self, event: Event, transformer: DataTransformer) -> None:
        async with self._lock:
            data = pickle.dumps(event.data)
            data = transformer.encode(data)
            await self._conn.execute(
                """
                INSERT OR REPLACE INTO events
                (id, type, data, source, priority, timestamp, ttl, retry_count, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.type,
                    data,
                    event.source,
                    event.priority.value,
                    event.timestamp,
                    event.ttl,
                    event.retry_count,
                    event.status.value,
                    json.dumps(event.metadata),
                ),
            )
            await self._conn.commit()

    async def load_all(self, transformer: DataTransformer) -> List[Event]:
        events = []
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT * FROM events ORDER BY timestamp ASC"
            )
            async for row in cursor:
                data = transformer.decode(row["data"])
                event_data = pickle.loads(data)
                event = Event(
                    id=row["id"],
                    type=row["type"],
                    data=event_data,
                    source=row["source"],
                    priority=EventPriority(row["priority"]),
                    timestamp=row["timestamp"],
                    ttl=row["ttl"],
                    retry_count=row["retry_count"],
                    status=EventStatus(row["status"]),
                    metadata=json.loads(row["metadata"]),
                )
                events.append(event)
        return events

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()


# ============================================================================
# EVENT SOURCING LOG
# ============================================================================


class EventSourcingLog:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not _is_aiosqlite_available():
            raise RuntimeError("aiosqlite niet beschikbaar")
        aiosqlite = _lazy_import("aiosqlite", "connect")
        self._conn = await aiosqlite(self.db_path)
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                action TEXT,
                timestamp REAL,
                details TEXT
            )
            """
        )
        await self._conn.commit()

    async def log(self, event_id: str, action: str, details: Optional[Dict] = None) -> None:
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO event_log (event_id, action, timestamp, details) VALUES (?, ?, ?, ?)",
                (event_id, action, time.time(), json.dumps(details or {})),
            )
            await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()


# ============================================================================
# MEMORY BACKEND
# ============================================================================


class MemoryBackend:
    def __init__(self):
        self._subscribers: Dict[str, List[Subscription]] = defaultdict(list)

    async def publish(self, channel: str, message: bytes) -> None:
        event = pickle.loads(message)
        for sub in self._subscribers.get(channel, []):
            asyncio.create_task(self._deliver(sub, event))

    async def _deliver(self, sub: Subscription, event: Event) -> None:
        try:
            await sub.callback(event)
        except Exception as e:
            logger.error(f"Subscriber callback mislukt: {e}")

    async def subscribe(self, channel: str, subscription: Subscription) -> None:
        self._subscribers[channel].append(subscription)

    async def close(self) -> None:
        pass


# ============================================================================
# REDIS BACKEND
# ============================================================================


class RedisBackend:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Any = None
        self._pubsub: Any = None
        self._subscribers: Dict[str, List[Subscription]] = defaultdict(list)

    async def _ensure_client(self):
        if self._client is None:
            redis = _lazy_import("redis.asyncio", "Redis")
            if redis is None:
                raise RuntimeError("Redis niet beschikbaar")
            self._client = await redis.from_url(self.redis_url)
            self._pubsub = self._client.pubsub()
        return self._client

    async def publish(self, channel: str, message: bytes) -> None:
        client = await self._ensure_client()
        await client.publish(channel, message)

    async def subscribe(self, channel: str, subscription: Subscription) -> None:
        self._subscribers[channel].append(subscription)
        if self._pubsub:
            await self._pubsub.subscribe(channel)
            asyncio.create_task(self._listen(channel))

    async def _listen(self, channel: str):
        while True:
            try:
                message = await self._pubsub.get_message(timeout=1.0, ignore_subscribe_messages=True)
                if message:
                    event = pickle.loads(message["data"])
                    for sub in self._subscribers[channel]:
                        asyncio.create_task(self._deliver(sub, event))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Redis listener fout: {e}")

    async def _deliver(self, sub: Subscription, event: Event):
        try:
            await sub.callback(event)
        except Exception as e:
            logger.error(f"Subscriber callback mislukt: {e}")

    async def close(self) -> None:
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()


# ============================================================================
# EVENT BUS
# ============================================================================


class EventBus:
    def __init__(self, config: Optional[EventBusConfig] = None) -> None:
        self.config = config or EventBusConfig()
        self.node_id = self.config.node_id
        self._active = False

        # Subscribers
        self._subscribers: Dict[str, List[Subscription]] = defaultdict(list)

        # Queues
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=self.config.max_queue_size)
        self._dead_letter: deque[Tuple[Event, Exception]] = deque(maxlen=self.config.dead_letter_max_size)

        # Backend
        self._backend: EventBackend = self._create_backend()

        # Serializer
        self._serializer = self._create_serializer()

        # Data transformer (encryptie/compressie)
        self._transformer = DataTransformer(self.config)

        # Persistentie
        self._store: Optional[EventStore] = None
        if self.config.enable_persistence:
            self._store = EventStore(self.config.persistence_path)

        # Event sourcing
        self._sourcing: Optional[EventSourcingLog] = None
        if self.config.enable_event_sourcing:
            self._sourcing = EventSourcingLog(self.config.sourcing_path)

        # Schema registry
        self._schemas: Dict[str, Dict[str, Any]] = {}

        # Routing
        self._routes: Dict[str, List[EventBus]] = defaultdict(list)

        # Transformaties
        self._transformers: Dict[str, List[Callable[[Event], Event]]] = defaultdict(list)

        # Filters
        self._filters: Dict[str, List[Callable[[Event], bool]]] = defaultdict(list)

        # Rate limiter
        self._tokens = self.config.rate_limit or float("inf")
        self._last_refill = time.monotonic()

        # Metrics
        self._setup_metrics()

        # History
        self._history: deque[Event] = deque(maxlen=self.config.max_history)

        # Tasks
        self._main_task: Optional[asyncio.Task] = None
        self._batch_task: Optional[asyncio.Task] = None

        logger.info(f"🌊 EventBus {self.node_id} geïnitialiseerd")

    def _create_backend(self) -> EventBackend:
        if self.config.enable_distributed and self.config.distributed_backend == "redis":
            if _is_redis_available():
                return RedisBackend(self.config.redis_url)
            else:
                logger.warning("Redis niet beschikbaar – val terug op memory backend")
        return MemoryBackend()

    def _create_serializer(self) -> EventSerializer:
        if self.config.serializer == "json":
            return JSONSerializer()
        elif self.config.serializer == "pickle":
            return PickleSerializer()
        elif self.config.serializer == "msgpack" and _is_msgpack_available():
            return MsgPackSerializer()
        return JSONSerializer()

    def _setup_metrics(self) -> None:
        if not _is_prometheus_available() or not self.config.enable_prometheus:
            return
        try:
            Counter = _lazy_import("prometheus_client", "Counter")
            Histogram = _lazy_import("prometheus_client", "Histogram")
            Gauge = _lazy_import("prometheus_client", "Gauge")
            start_http_server = _lazy_import("prometheus_client", "start_http_server")
            if start_http_server and self.config.prometheus_port:
                start_http_server(self.config.prometheus_port)
            self._metric_events = Counter(
                "eventbus_events_total", "Total events", ["type", "priority", "status"]
            )
            self._metric_processing = Histogram("eventbus_processing_seconds", "Processing time")
            self._metric_queue = Gauge("eventbus_queue_size", "Queue size")
            self._metric_subscribers = Gauge(
                "eventbus_subscribers", "Number of subscribers", ["event_type"]
            )
        except Exception as e:
            logger.warning(f"Prometheus setup mislukt: {e}")

    # ------------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------------
    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], Awaitable[None]],
        priority: int = 0,
        filter_func: Optional[Callable[[Event], bool]] = None,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker: Optional[CircuitBreakerConfig] = None,
    ) -> None:
        sub = Subscription(
            callback=callback,
            priority=priority,
            filter_func=filter_func,
            retry_policy=retry_policy or self.config.retry_policy,
            circuit_breaker=CircuitBreaker(circuit_breaker or self.config.circuit_breaker),
        )
        self._subscribers[event_type].append(sub)
        self._subscribers[event_type].sort(key=lambda s: s.priority, reverse=True)

        if hasattr(self, "_metric_subscribers"):
            self._metric_subscribers.labels(event_type=event_type).inc()

        if hasattr(self._backend, "subscribe"):
            asyncio.create_task(self._backend.subscribe(event_type, sub))

    async def emit(
        self,
        event_type: str,
        data: Any,
        source: str,
        priority: EventPriority = EventPriority.NORMAL,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if not self._check_rate_limit():
            logger.warning("Rate limit overschreden – event gedropt")
            return None

        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            source=source,
            priority=priority,
            ttl=ttl,
            metadata=metadata or {},
        )

        # Schema validatie
        if self.config.enable_schema_registry and event_type in self._schemas:
            if not self._validate_schema(event, self._schemas[event_type]):
                logger.error(f"Event {event.id} voldoet niet aan schema")
                return None

        # Opslaan in persistentie
        if self._store:
            await self._store.save(event, self._transformer)

        # Event sourcing log
        if self._sourcing:
            await self._sourcing.log(event.id, "emit", {"source": source})

        # In queue
        try:
            await self._queue.put(event)
        except asyncio.QueueFull:
            logger.error("Event queue vol – event gedropt")
            return None

        if hasattr(self, "_metric_events"):
            self._metric_events.labels(type=event_type, priority=priority.name, status="emitted").inc()

        return event.id

    def register_schema(self, event_type: str, schema: Dict[str, Any]) -> None:
        self._schemas[event_type] = schema

    def _validate_schema(self, event: Event, schema: Dict[str, Any]) -> bool:
        # Eenvoudige validatie: controleer aanwezigheid van verplichte velden
        required = schema.get("required", [])
        for field in required:
            if field not in event.metadata:
                return False
        return True

    def add_route(self, event_type: str, target_bus: "EventBus") -> None:
        self._routes[event_type].append(target_bus)

    def add_transformer(self, event_type: str, transformer: Callable[[Event], Event]) -> None:
        self._transformers[event_type].append(transformer)

    def add_filter(self, event_type: str, filter_func: Callable[[Event], bool]) -> None:
        self._filters[event_type].append(filter_func)

    # ------------------------------------------------------------------------
    # Interne verwerking
    # ------------------------------------------------------------------------
    def _check_rate_limit(self) -> bool:
        if self.config.rate_limit is None:
            return True
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.config.rate_limit, self._tokens + elapsed * self.config.rate_limit)
        self._last_refill = now
        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False

    async def start(self) -> None:
        self._active = True
        if self._store:
            await self._store.connect()
        if self._sourcing:
            await self._sourcing.connect()
        self._main_task = asyncio.create_task(self._run())
        if self.config.batch_size > 0:
            self._batch_task = asyncio.create_task(self._batch_processor())
        logger.info(f"🚀 EventBus {self.node_id} gestart")

    async def _run(self) -> None:
        while self._active:
            try:
                if hasattr(self, "_metric_queue"):
                    self._metric_queue.set(self._queue.qsize())
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                await self._process_event(event)
                self._history.append(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.exception(f"Fout in event loop: {e}")

    async def _process_event(self, event: Event) -> None:
        if event.is_expired():
            event.status = EventStatus.EXPIRED
            return

        # Filters
        if not self._apply_filters(event):
            return

        # Transformaties
        event = self._apply_transformers(event)

        # Routing
        await self._route_event(event)

        # Bezorging aan subscribers
        subscribers = self._subscribers.get(event.type, [])
        if not subscribers:
            return

        # Publiceer naar distributed backend
        if self.config.enable_distributed:
            serialized = self._serializer.serialize(event)
            await self._backend.publish(event.type, serialized)

        for sub in subscribers:
            if sub.filter_func and not sub.filter_func(event):
                continue
            if not sub.circuit_breaker.allow_request():
                continue

            start = time.perf_counter()
            success = False
            try:
                await self._invoke_with_retry(sub, event)
                sub.circuit_breaker.record_success()
                success = True
            except Exception as e:
                sub.circuit_breaker.record_failure()
                sub.error_count += 1
                self._dead_letter.append((event, e))
                event.status = EventStatus.DEAD_LETTER
                logger.error(f"Subscriber definitief gefaald voor {event.id}: {e}")
            finally:
                duration = time.perf_counter() - start
                sub.avg_duration = 0.3 * duration + 0.7 * sub.avg_duration
                sub.call_count += 1
                if hasattr(self, "_metric_processing"):
                    self._metric_processing.observe(duration)

    async def _invoke_with_retry(self, sub: Subscription, event: Event) -> None:
        policy = sub.retry_policy
        for attempt in range(policy.max_retries):
            try:
                await sub.callback(event)
                return
            except policy.retry_on as e:
                if attempt == policy.max_retries - 1:
                    raise
                delay = min(policy.backoff_factor**attempt, policy.max_delay)
                await asyncio.sleep(delay)

    def _apply_filters(self, event: Event) -> bool:
        for filter_func in self._filters.get(event.type, []):
            if not filter_func(event):
                return False
        return True

    def _apply_transformers(self, event: Event) -> Event:
        for transformer in self._transformers.get(event.type, []):
            try:
                event = transformer(event)
            except Exception as e:
                logger.error(f"Transformer fout: {e}")
        return event

    async def _route_event(self, event: Event) -> None:
        for target in self._routes.get(event.type, []):
            try:
                await target.emit(
                    event_type=event.type,
                    data=event.data,
                    source=f"{self.node_id}->{target.node_id}",
                    priority=event.priority,
                    ttl=event.ttl,
                    metadata=event.metadata,
                )
            except Exception as e:
                logger.error(f"Routing fout naar {target.node_id}: {e}")

    async def _batch_processor(self) -> None:
        while self._active:
            try:
                batch: List[Event] = []
                deadline = time.monotonic() + self.config.batch_timeout
                while len(batch) < self.config.batch_size and time.monotonic() < deadline:
                    try:
                        event = await asyncio.wait_for(
                            self._queue.get(), timeout=deadline - time.monotonic()
                        )
                        batch.append(event)
                    except asyncio.TimeoutError:
                        break
                for event in batch:
                    await self._process_event(event)
                    self._history.append(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Batch processor fout: {e}")

    async def stop(self) -> None:
        self._active = False
        if self._main_task:
            self._main_task.cancel()
        if self._batch_task:
            self._batch_task.cancel()
        await self._backend.close()
        if self._store:
            await self._store.close()
        if self._sourcing:
            await self._sourcing.close()
        logger.info(f"🛑 EventBus {self.node_id} gestopt")

    # ------------------------------------------------------------------------
    # Dead letter & Replay
    # ------------------------------------------------------------------------
    def get_dead_letter(self) -> List[Tuple[Event, Exception]]:
        return list(self._dead_letter)

    async def retry_dead_letter(self, max_retry: int = 3) -> int:
        retried = 0
        remaining: List[Tuple[Event, Exception]] = []
        for event, _ in self._dead_letter:
            if event.retry_count < max_retry:
                event.retry_count += 1
                event.status = EventStatus.PENDING
                await self._queue.put(event)
                retried += 1
            else:
                remaining.append((event, _))
        self._dead_letter = deque(remaining, maxlen=self.config.dead_letter_max_size)
        logger.info(f"🔄 {retried} events opnieuw in queue")
        return retried

    async def replay(self, from_time: float, to_time: Optional[float] = None) -> None:
        if not self._store:
            logger.warning("Persistentie niet ingeschakeld – replay onmogelijk")
            return
        events = await self._store.load_all(self._transformer)
        to_time = to_time or time.time()
        for event in events:
            if from_time <= event.timestamp <= to_time:
                await self._process_event(event)
        logger.info(f"🔄 Replay voltooid ({from_time} → {to_time})")

    # ------------------------------------------------------------------------
    # Statistieken
    # ------------------------------------------------------------------------
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [
            {
                "id": e.id,
                "type": e.type,
                "source": e.source,
                "timestamp": e.timestamp,
                "status": e.status.value,
            }
            for e in list(self._history)[-limit:]
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "queue_size": self._queue.qsize(),
            "subscribers": sum(len(v) for v in self._subscribers.values()),
            "dead_letter": len(self._dead_letter),
            "history": len(self._history),
            "persistence": self.config.enable_persistence,
            "distributed": self.config.enable_distributed,
        }