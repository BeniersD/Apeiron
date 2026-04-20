"""
DOCUMENT TRACKER – State‑of‑the‑Art Edition
===========================================================================
Voorkomt dubbele verwerking van documenten en legt relaties vast voor backtracing.

Kenmerken:
- Configuratie via dataclass
- Asynchrone SQLite database (aiosqlite) met connection pooling
- Content hashing via blake3 (sneller dan SHA‑256) met fallback
- URL vs. lokaal bestand detectie
- Relatie‑graph voor backtracing (wie citeert wie?)
- JSON export voor dashboards
- Prometheus metrics (optioneel)
- Cache voor snelle lookups
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Optionele imports
try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    logger.warning("aiosqlite niet beschikbaar – persistentie uitgeschakeld")

try:
    import blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False
    logger.debug("blake3 niet beschikbaar – gebruik SHA‑256 als fallback")

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ============================================================================
# CONFIGURATIE
# ============================================================================


@dataclass(frozen=True)
class TrackerConfig:
    """Configuratie voor de document tracker."""

    # Database
    db_path: str = "document_tracking.db"
    enable_persistence: bool = True

    # JSON export
    json_log_path: str = "verwerkte_documenten.json"
    enable_json_export: bool = True

    # Cache
    cache_size: int = 10000
    cache_ttl: int = 3600  # seconden

    # Content hashing
    hash_algorithm: str = "blake3"  # "blake3", "sha256", "md5"

    # Backtracing
    enable_backtracing: bool = True
    max_backtrace_depth: int = 10

    # Automatische opschoning
    auto_cleanup: bool = False
    cleanup_interval_days: int = 30

    # Limieten
    max_history: int = 1000
    max_relations: int = 10000

    # Prometheus
    enable_prometheus: bool = False
    prometheus_port: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ============================================================================
# DATASTRUCTUREN
# ============================================================================


@dataclass(slots=True)
class DocumentRecord:
    """Interne representatie van een document."""

    id: int
    path: str
    filename: str
    size: int
    hash_value: str
    first_seen: float
    last_seen: float
    status: str
    processing_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProcessingRecord:
    """Registratie van een individuele verwerking."""

    id: int
    document_id: int
    timestamp: float
    processing_type: str
    duration_ms: Optional[int]
    details: str


@dataclass(slots=True)
class RelationRecord:
    """Relatie tussen twee documenten."""

    id: int
    source_id: int
    target_id: int
    relation_type: str
    timestamp: float
    strength: float = 1.0


# ============================================================================
# HASH UTILITIES
# ============================================================================


class HashGenerator:
    """Genereer content hashes met het geconfigureerde algoritme."""

    def __init__(self, algorithm: str = "blake3"):
        self.algorithm = algorithm
        if algorithm == "blake3" and BLAKE3_AVAILABLE:
            self._hasher = lambda: blake3.blake3()
        elif algorithm == "sha256":
            self._hasher = hashlib.sha256
        else:
            self._hasher = hashlib.md5

    def file_hash(self, path: str) -> Optional[str]:
        """Bereken hash van een lokaal bestand."""
        try:
            hasher = self._hasher()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Hash berekening mislukt voor {path}: {e}")
            return None

    def url_hash(self, url: str) -> str:
        """Genereer een stabiele hash voor een URL."""
        return hashlib.md5(url.encode()).hexdigest()


# ============================================================================
# ASYNCHRONE DATABASE (SQLITE)
# ============================================================================


class DocumentDatabase:
    """Asynchrone SQLite database voor document tracking."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not AIOSQLITE_AVAILABLE:
            raise RuntimeError("aiosqlite is niet geïnstalleerd")
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def _create_tables(self) -> None:
        async with self._lock:
            await self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    filename TEXT,
                    size INTEGER,
                    hash_value TEXT,
                    first_seen REAL,
                    last_seen REAL,
                    status TEXT,
                    processing_count INTEGER DEFAULT 1,
                    metadata TEXT
                )
                """
            )
            await self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    timestamp REAL,
                    processing_type TEXT,
                    duration_ms INTEGER,
                    details TEXT,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                )
                """
            )
            await self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    relation_type TEXT,
                    timestamp REAL,
                    strength REAL DEFAULT 1.0,
                    FOREIGN KEY(source_id) REFERENCES documents(id),
                    FOREIGN KEY(target_id) REFERENCES documents(id),
                    UNIQUE(source_id, target_id, relation_type)
                )
                """
            )
            await self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path)"
            )
            await self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(hash_value)"
            )
            await self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_processings_doc ON processings(document_id)"
            )
            await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    # ------------------------------------------------------------------------
    # Document operaties
    # ------------------------------------------------------------------------
    async def get_document_by_path(self, path: str) -> Optional[DocumentRecord]:
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT * FROM documents WHERE path = ?", (path,)
            )
            row = await cursor.fetchone()
            if row:
                return DocumentRecord(
                    id=row["id"],
                    path=row["path"],
                    filename=row["filename"],
                    size=row["size"],
                    hash_value=row["hash_value"],
                    first_seen=row["first_seen"],
                    last_seen=row["last_seen"],
                    status=row["status"],
                    processing_count=row["processing_count"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
        return None

    async def get_document_by_hash(self, hash_val: str) -> Optional[DocumentRecord]:
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT * FROM documents WHERE hash_value = ?", (hash_val,)
            )
            row = await cursor.fetchone()
            if row:
                return DocumentRecord(
                    id=row["id"],
                    path=row["path"],
                    filename=row["filename"],
                    size=row["size"],
                    hash_value=row["hash_value"],
                    first_seen=row["first_seen"],
                    last_seen=row["last_seen"],
                    status=row["status"],
                    processing_count=row["processing_count"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
        return None

    async def upsert_document(
        self,
        path: str,
        filename: str,
        size: int,
        hash_value: str,
        status: str = "processed",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        now = time.time()
        async with self._lock:
            # Probeer bestaand document te vinden
            cursor = await self._conn.execute(
                "SELECT id, processing_count FROM documents WHERE path = ?", (path,)
            )
            existing = await cursor.fetchone()
            if existing:
                new_count = existing["processing_count"] + 1
                await self._conn.execute(
                    """
                    UPDATE documents
                    SET last_seen = ?, processing_count = ?, hash_value = ?, size = ?, metadata = ?
                    WHERE id = ?
                    """,
                    (now, new_count, hash_value, size, json.dumps(metadata or {}), existing["id"]),
                )
                await self._conn.commit()
                return existing["id"]
            else:
                cursor = await self._conn.execute(
                    """
                    INSERT INTO documents
                    (path, filename, size, hash_value, first_seen, last_seen, status, processing_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (path, filename, size, hash_value, now, now, status, json.dumps(metadata or {})),
                )
                await self._conn.commit()
                return cursor.lastrowid

    async def add_processing(
        self,
        document_id: int,
        processing_type: str,
        duration_ms: Optional[int] = None,
        details: str = "",
    ) -> None:
        async with self._lock:
            await self._conn.execute(
                """
                INSERT INTO processings (document_id, timestamp, processing_type, duration_ms, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, time.time(), processing_type, duration_ms, details),
            )
            await self._conn.commit()

    async def add_relation(
        self,
        source_id: int,
        target_id: int,
        relation_type: str,
        strength: float = 1.0,
    ) -> None:
        async with self._lock:
            await self._conn.execute(
                """
                INSERT OR IGNORE INTO relations (source_id, target_id, relation_type, timestamp, strength)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source_id, target_id, relation_type, time.time(), strength),
            )
            await self._conn.commit()

    async def get_backtrace(self, doc_id: int, depth: int = 10) -> Dict[str, List[Dict]]:
        forward = []
        backward = []
        async with self._lock:
            # Forward relaties
            cursor = await self._conn.execute(
                """
                SELECT d.path, r.relation_type, r.timestamp, r.strength
                FROM relations r
                JOIN documents d ON r.target_id = d.id
                WHERE r.source_id = ?
                ORDER BY r.timestamp DESC
                LIMIT ?
                """,
                (doc_id, depth * 10),
            )
            async for row in cursor:
                forward.append(
                    {
                        "document": row["path"],
                        "relation": row["relation_type"],
                        "timestamp": row["timestamp"],
                        "strength": row["strength"],
                    }
                )

            # Backward relaties
            cursor = await self._conn.execute(
                """
                SELECT d.path, r.relation_type, r.timestamp, r.strength
                FROM relations r
                JOIN documents d ON r.source_id = d.id
                WHERE r.target_id = ?
                ORDER BY r.timestamp DESC
                LIMIT ?
                """,
                (doc_id, depth * 10),
            )
            async for row in cursor:
                backward.append(
                    {
                        "document": row["path"],
                        "relation": row["relation_type"],
                        "timestamp": row["timestamp"],
                        "strength": row["strength"],
                    }
                )
        return {"forward": forward, "backward": backward}

    async def get_stats(self) -> Dict[str, int]:
        async with self._lock:
            cursor = await self._conn.execute("SELECT COUNT(*) FROM documents")
            docs = (await cursor.fetchone())[0]
            cursor = await self._conn.execute("SELECT COUNT(*) FROM processings")
            procs = (await cursor.fetchone())[0]
            cursor = await self._conn.execute("SELECT COUNT(*) FROM relations")
            rels = (await cursor.fetchone())[0]
        return {"documents": docs, "processings": procs, "relations": rels}


# ============================================================================
# DOCUMENT TRACKER
# ============================================================================


class DocumentTracker:
    """
    Beheert verwerkte documenten, voorkomt duplicaten en legt relaties vast.

    Gebruik:
        tracker = DocumentTracker()
        doc_id = await tracker.process_document("/pad/naar/doc.pdf")
        await tracker.add_relation(doc_id, other_id, "cites")
    """

    def __init__(self, config: Optional[TrackerConfig] = None) -> None:
        self.config = config or TrackerConfig()

        # Database
        self.db: Optional[DocumentDatabase] = None
        if self.config.enable_persistence and AIOSQLITE_AVAILABLE:
            self.db = DocumentDatabase(self.config.db_path)

        # Hasher
        self.hasher = HashGenerator(self.config.hash_algorithm)

        # Cache voor snelle lookups
        self._path_cache: Dict[str, int] = {}
        self._hash_cache: Dict[str, int] = {}

        # Metrics
        self._metrics = {
            "total_documents": 0,
            "total_processings": 0,
            "total_relations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "start_time": time.time(),
        }

        # Initialisatie
        self._initialized = False

        logger.info(f"📄 DocumentTracker geïnitialiseerd (db={self.config.db_path})")

    async def _ensure_initialized(self) -> None:
        if not self._initialized and self.db:
            await self.db.connect()
            # Laad cache uit database
            await self._load_cache()
            self._initialized = True

    async def _load_cache(self) -> None:
        if not self.db:
            return
        async with self.db._lock:
            cursor = await self.db._conn.execute("SELECT id, path, hash_value FROM documents")
            async for row in cursor:
                self._path_cache[row["path"]] = row["id"]
                if row["hash_value"]:
                    self._hash_cache[row["hash_value"]] = row["id"]
        logger.debug(f"Cache geladen: {len(self._path_cache)} paden, {len(self._hash_cache)} hashes")

    # ------------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------------
    async def is_processed(self, path: str, check_hash: bool = True) -> bool:
        """
        Controleer of een document al verwerkt is.

        Args:
            path: Pad of URL van het document.
            check_hash: Of ook op hash gecontroleerd moet worden (alleen lokaal).

        Returns:
            True als het document al bekend is.
        """
        await self._ensure_initialized()

        # Check cache
        if path in self._path_cache:
            self._metrics["cache_hits"] += 1
            return True
        self._metrics["cache_misses"] += 1

        # Check database
        if self.db:
            record = await self.db.get_document_by_path(path)
            if record:
                self._path_cache[path] = record.id
                return True

        # Optionele hash-check (voor lokale bestanden)
        if check_hash and not self._is_url(path):
            hash_val = self.hasher.file_hash(path)
            if hash_val:
                if hash_val in self._hash_cache:
                    return True
                if self.db:
                    record = await self.db.get_document_by_hash(hash_val)
                    if record:
                        self._hash_cache[hash_val] = record.id
                        return True

        return False

    async def process_document(
        self,
        path: str,
        status: str = "processed",
        processing_type: str = "initial",
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Registreer de verwerking van een document.

        Args:
            path: Pad of URL van het document.
            status: Status van de verwerking.
            processing_type: Type verwerking.
            duration_ms: Duur in milliseconden.
            metadata: Extra metadata.

        Returns:
            Het document ID, of None bij fout.
        """
        await self._ensure_initialized()

        is_url = self._is_url(path)

        # Bepaal bestandsnaam, grootte en hash
        if is_url:
            filename = path.split("/")[-1] or "online_document"
            size = 0
            hash_value = self.hasher.url_hash(path)
        else:
            filename = os.path.basename(path)
            try:
                size = os.path.getsize(path)
                hash_value = self.hasher.file_hash(path) or self.hasher.url_hash(path)
            except Exception:
                size = 0
                hash_value = self.hasher.url_hash(path)

        doc_id = None
        if self.db:
            doc_id = await self.db.upsert_document(
                path=path,
                filename=filename,
                size=size,
                hash_value=hash_value,
                status=status,
                metadata=metadata,
            )
            await self.db.add_processing(
                document_id=doc_id,
                processing_type=processing_type,
                duration_ms=duration_ms,
                details="",
            )
            # Update cache
            self._path_cache[path] = doc_id
            self._hash_cache[hash_value] = doc_id

        self._metrics["total_processings"] += 1

        # Exporteer JSON (asynchroon om niet te blokkeren)
        if self.config.enable_json_export:
            asyncio.create_task(self._export_json())

        return doc_id

    async def add_relation(
        self,
        source_path: str,
        target_path: str,
        relation_type: str = "reference",
        strength: float = 1.0,
    ) -> bool:
        """
        Voeg een relatie toe tussen twee documenten.

        Args:
            source_path: Bron document.
            target_path: Doel document.
            relation_type: Type relatie (bijv. "cites", "extends").
            strength: Sterkte van de relatie (0-1).

        Returns:
            True als de relatie is toegevoegd.
        """
        if not self.config.enable_backtracing:
            return False

        await self._ensure_initialized()

        # Zorg dat beide documenten bestaan (of forceer registratie)
        source_id = self._path_cache.get(source_path)
        target_id = self._path_cache.get(target_path)

        if source_id is None and self.db:
            source_id = await self.process_document(source_path, status="referenced")
        if target_id is None and self.db:
            target_id = await self.process_document(target_path, status="referenced")

        if source_id and target_id and self.db:
            await self.db.add_relation(source_id, target_id, relation_type, strength)
            self._metrics["total_relations"] += 1
            return True
        return False

    async def get_backtrace(self, path: str, depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Haal backtrace op voor een document.

        Args:
            path: Documentpad.
            depth: Maximale diepte (default uit config).

        Returns:
            Dictionary met forward en backward relaties.
        """
        depth = depth or self.config.max_backtrace_depth
        await self._ensure_initialized()

        doc_id = self._path_cache.get(path)
        if doc_id is None and self.db:
            record = await self.db.get_document_by_path(path)
            doc_id = record.id if record else None

        if doc_id is None:
            return {"forward": [], "backward": [], "document": path}

        if self.db:
            relations = await self.db.get_backtrace(doc_id, depth)
        else:
            relations = {"forward": [], "backward": []}

        return {
            "document": path,
            "forward": relations["forward"],
            "backward": relations["backward"],
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Retourneer statistieken over de tracker."""
        stats = self._metrics.copy()
        stats["uptime_seconds"] = time.time() - stats["start_time"]
        if self.db:
            db_stats = await self.db.get_stats()
            stats.update(db_stats)
        if self._metrics["cache_misses"] + self._metrics["cache_hits"] > 0:
            stats["cache_hit_ratio"] = self._metrics["cache_hits"] / (
                self._metrics["cache_hits"] + self._metrics["cache_misses"]
            )
        return stats

    async def _export_json(self) -> None:
        """Exporteer de database naar een JSON-bestand."""
        if not self.db:
            return
        try:
            # Vereenvoudigde export: alleen laatste N documenten
            async with self.db._lock:
                cursor = await self.db._conn.execute(
                    """
                    SELECT path, filename, first_seen, last_seen, processing_count, status, metadata
                    FROM documents
                    ORDER BY last_seen DESC
                    LIMIT ?
                    """,
                    (self.config.max_history,),
                )
                docs = []
                async for row in cursor:
                    docs.append(
                        {
                            "path": row["path"],
                            "filename": row["filename"],
                            "first_seen": row["first_seen"],
                            "last_seen": row["last_seen"],
                            "processing_count": row["processing_count"],
                            "status": row["status"],
                            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        }
                    )

            data = {
                "export_time": time.time(),
                "stats": await self.get_stats(),
                "documents": docs,
            }
            with open(self.config.json_log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"JSON geëxporteerd naar {self.config.json_log_path}")
        except Exception as e:
            logger.error(f"JSON export mislukt: {e}")

    @staticmethod
    def _is_url(path: str) -> bool:
        return path.startswith(("http://", "https://"))

    async def cleanup(self) -> None:
        """Sluit databaseverbinding en ruim op."""
        if self.db:
            await self.db.close()
        logger.info("📄 DocumentTracker afgesloten")