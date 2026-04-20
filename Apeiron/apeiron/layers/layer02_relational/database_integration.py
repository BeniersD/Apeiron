"""
DATABASE INTEGRATION – ULTIMATE IMPLEMENTATION
===============================================
This module provides a unified interface for storing and loading Layer 2 objects
(UltimateRelation, Hypergraph, TopologicalNetworkAnalysis, etc.) in various databases.

Supported backends:
- SQLite (built‑in)
- PostgreSQL (via SQLAlchemy + asyncpg or psycopg2)
- Neo4j (graph database)
- MongoDB (document store)
- Redis (cache / key‑value store)

All backends are optional; the module degrades gracefully if required drivers are missing.
Serialization of numpy arrays and complex numbers is handled via pickle or custom JSON encoders.

The main class `DatabaseManager` provides high‑level methods to store/load objects by ID.
It also supports an optional Redis cache to speed up repeated reads.
"""

import logging
import pickle
import json
import numpy as np
from typing import Optional, Dict, List, Any, Union, Type, Iterable
from abc import ABC, abstractmethod
from datetime import datetime

# ============================================================================
# OPTIONAL LIBRARIES – HANDLED GRACEFULLY
# ============================================================================

# SQLite (always available in Python)
import sqlite3

# PostgreSQL via asyncpg (async) or psycopg2 (sync)
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# SQLAlchemy core (optional, for PostgreSQL abstraction)
try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker, declarative_base
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Neo4j driver
try:
    from neo4j import GraphDatabase, AsyncGraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

# MongoDB driver
try:
    import motor.motor_asyncio
    import pymongo
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

# Redis for caching (optional)
try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

# NetworkX (optional, for resonance graphs)
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM JSON ENCODER FOR NUMPY/COMPLEX
# ============================================================================

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy arrays and complex numbers."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, complex):
            return {'__complex__': True, 'real': obj.real, 'imag': obj.imag}
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def decode_numpy(dct):
    """Decode dict back to numpy/complex."""
    if '__complex__' in dct:
        return complex(dct['real'], dct['imag'])
    return dct


# ============================================================================
# CACHE INTERFACE
# ============================================================================

class CacheBackend(ABC):
    """Abstract base for a simple key‑value cache."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        pass

    @abstractmethod
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Retrieve multiple values by keys."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store a value with optional time‑to‑live (seconds)."""
        pass

    @abstractmethod
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None):
        """Store multiple key‑value pairs (implementation may ignore ttl per key)."""
        pass

    @abstractmethod
    async def delete(self, key: str):
        """Remove a key."""
        pass

    @abstractmethod
    async def close(self):
        """Close the connection."""
        pass


if HAS_REDIS:
    class RedisCache(CacheBackend):
        """Redis cache backend using redis.asyncio."""

        def __init__(self, url: str = "redis://localhost:6379", default_ttl: int = 3600):
            self.url = url
            self.default_ttl = default_ttl
            self.client = None

        async def connect(self):
            self.client = redis.from_url(self.url, decode_responses=False)  # keep bytes for pickle

        async def close(self):
            if self.client:
                await self.client.close()

        async def get(self, key: str) -> Optional[Any]:
            data = await self.client.get(key)
            if data:
                try:
                    return pickle.loads(data)
                except Exception:
                    logger.warning("Failed to unpickle cache key %s", key)
            return None

        async def mget(self, keys: List[str]) -> List[Optional[Any]]:
            if not keys:
                return []
            data_list = await self.client.mget(*keys)
            result = []
            for data in data_list:
                if data:
                    try:
                        result.append(pickle.loads(data))
                    except Exception:
                        result.append(None)
                else:
                    result.append(None)
            return result

        async def set(self, key: str, value: Any, ttl: Optional[int] = None):
            data = pickle.dumps(value)
            ttl = ttl if ttl is not None else self.default_ttl
            await self.client.setex(key, ttl, data)

        async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None):
            # Redis pipeline with setex for each key
            ttl = ttl if ttl is not None else self.default_ttl
            async with self.client.pipeline() as pipe:
                for key, value in mapping.items():
                    data = pickle.dumps(value)
                    await pipe.setex(key, ttl, data)
                await pipe.execute()

        async def delete(self, key: str):
            await self.client.delete(key)

else:
    class RedisCache(CacheBackend):
        def __init__(self, *args, **kwargs):
            raise ImportError("Redis driver (redis.asyncio) is required for Redis cache")

    HAS_REDIS = False  # ensure it's consistent


# ============================================================================
# ABSTRACT BASE CLASS FOR DATABASE BACKENDS
# ============================================================================

class DatabaseBackend(ABC):
    """Abstract base class for all database backends."""

    @abstractmethod
    async def connect(self):
        """Establish connection to the database."""
        pass

    @abstractmethod
    async def close(self):
        """Close the connection."""
        pass

    @abstractmethod
    async def store_relation(self, relation: 'UltimateRelation'):
        """Store a single UltimateRelation."""
        pass

    @abstractmethod
    async def load_relation(self, relation_id: str) -> Optional['UltimateRelation']:
        """Load a relation by ID."""
        pass

    @abstractmethod
    async def store_hypergraph(self, hypergraph: 'Hypergraph', name: str):
        """Store a hypergraph with a given name."""
        pass

    @abstractmethod
    async def load_hypergraph(self, name: str) -> Optional['Hypergraph']:
        """Load a hypergraph by name."""
        pass

    @abstractmethod
    async def store_analysis(self, analysis: 'TopologicalNetworkAnalysis', name: str):
        """Store a topological analysis result."""
        pass

    @abstractmethod
    async def load_analysis(self, name: str) -> Optional['TopologicalNetworkAnalysis']:
        """Load an analysis result by name."""
        pass

    # New methods for Layer 1 registries
    @abstractmethod
    async def save_layer1_registry(self, registry: Dict[str, Any], name: str):
        """Store a Layer 1 registry (dictionary of observables) with a given name."""
        pass

    @abstractmethod
    async def load_layer1_registry(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a Layer 1 registry by name."""
        pass

    # Batch operations
    @abstractmethod
    async def store_relations(self, relations: List['UltimateRelation']):
        """Store multiple relations in one batch."""
        pass

    @abstractmethod
    async def load_relations(self, relation_ids: List[str]) -> List[Optional['UltimateRelation']]:
        """Load multiple relations by IDs."""
        pass

    @abstractmethod
    async def store_hypergraphs(self, hypergraphs: Dict[str, 'Hypergraph']):
        """Store multiple hypergraphs (name -> object)."""
        pass

    @abstractmethod
    async def load_hypergraphs(self, names: List[str]) -> List[Optional['Hypergraph']]:
        """Load multiple hypergraphs by names."""
        pass

    @abstractmethod
    async def store_analyses(self, analyses: Dict[str, 'TopologicalNetworkAnalysis']):
        """Store multiple analyses (name -> object)."""
        pass

    @abstractmethod
    async def load_analyses(self, names: List[str]) -> List[Optional['TopologicalNetworkAnalysis']]:
        """Load multiple analyses by names."""
        pass


# ============================================================================
# SQLITE BACKEND (with batch support)
# ============================================================================

class SQLiteBackend(DatabaseBackend):
    """SQLite backend using pickle for serialization."""

    def __init__(self, db_path: str = "layer2.db"):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        """SQLite connection is synchronous; we run in thread pool."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                data BLOB,
                created_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hypergraphs (
                name TEXT PRIMARY KEY,
                data BLOB,
                created_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                name TEXT PRIMARY KEY,
                data BLOB,
                created_at TIMESTAMP
            )
        """)
        # New table for Layer 1 registries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS layer1_registries (
                name TEXT PRIMARY KEY,
                data BLOB,
                created_at TIMESTAMP
            )
        """)
        self.conn.commit()

    async def close(self):
        if self.conn:
            self.conn.close()

    async def store_relation(self, relation):
        data = pickle.dumps(relation)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO relations (id, data, created_at) VALUES (?, ?, ?)",
            (relation.id, data, datetime.utcnow())
        )
        self.conn.commit()

    async def load_relation(self, relation_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM relations WHERE id = ?", (relation_id,))
        row = cursor.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    async def store_hypergraph(self, hypergraph, name):
        data = pickle.dumps(hypergraph)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO hypergraphs (name, data, created_at) VALUES (?, ?, ?)",
            (name, data, datetime.utcnow())
        )
        self.conn.commit()

    async def load_hypergraph(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM hypergraphs WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    async def store_analysis(self, analysis, name):
        data = pickle.dumps(analysis)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO analyses (name, data, created_at) VALUES (?, ?, ?)",
            (name, data, datetime.utcnow())
        )
        self.conn.commit()

    async def load_analysis(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM analyses WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    # New methods for Layer 1 registries
    async def save_layer1_registry(self, registry, name):
        data = pickle.dumps(registry)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO layer1_registries (name, data, created_at) VALUES (?, ?, ?)",
            (name, data, datetime.utcnow())
        )
        self.conn.commit()

    async def load_layer1_registry(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM layer1_registries WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    # Batch operations
    async def store_relations(self, relations):
        cursor = self.conn.cursor()
        now = datetime.utcnow()
        data_list = [(r.id, pickle.dumps(r), now) for r in relations]
        cursor.executemany(
            "INSERT OR REPLACE INTO relations (id, data, created_at) VALUES (?, ?, ?)",
            data_list
        )
        self.conn.commit()

    async def load_relations(self, relation_ids):
        if not relation_ids:
            return []
        placeholders = ','.join(['?'] * len(relation_ids))
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id, data FROM relations WHERE id IN ({placeholders})", relation_ids)
        rows = cursor.fetchall()
        data_map = {row['id']: row['data'] for row in rows}
        result = []
        for rid in relation_ids:
            data = data_map.get(rid)
            result.append(pickle.loads(data) if data else None)
        return result

    async def store_hypergraphs(self, hypergraphs):
        cursor = self.conn.cursor()
        now = datetime.utcnow()
        data_list = [(name, pickle.dumps(hg), now) for name, hg in hypergraphs.items()]
        cursor.executemany(
            "INSERT OR REPLACE INTO hypergraphs (name, data, created_at) VALUES (?, ?, ?)",
            data_list
        )
        self.conn.commit()

    async def load_hypergraphs(self, names):
        if not names:
            return []
        placeholders = ','.join(['?'] * len(names))
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT name, data FROM hypergraphs WHERE name IN ({placeholders})", names)
        rows = cursor.fetchall()
        data_map = {row['name']: row['data'] for row in rows}
        result = []
        for name in names:
            data = data_map.get(name)
            result.append(pickle.loads(data) if data else None)
        return result

    async def store_analyses(self, analyses):
        cursor = self.conn.cursor()
        now = datetime.utcnow()
        data_list = [(name, pickle.dumps(an), now) for name, an in analyses.items()]
        cursor.executemany(
            "INSERT OR REPLACE INTO analyses (name, data, created_at) VALUES (?, ?, ?)",
            data_list
        )
        self.conn.commit()

    async def load_analyses(self, names):
        if not names:
            return []
        placeholders = ','.join(['?'] * len(names))
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT name, data FROM analyses WHERE name IN ({placeholders})", names)
        rows = cursor.fetchall()
        data_map = {row['name']: row['data'] for row in rows}
        result = []
        for name in names:
            data = data_map.get(name)
            result.append(pickle.loads(data) if data else None)
        return result


# ============================================================================
# POSTGRESQL BACKEND (using SQLAlchemy) with batch support
# ============================================================================

if HAS_SQLALCHEMY:
    Base = declarative_base()

    class RelationTable(Base):
        __tablename__ = 'relations'
        id = sa.Column(sa.String, primary_key=True)
        data = sa.Column(sa.LargeBinary)
        created_at = sa.Column(sa.DateTime)

    class HypergraphTable(Base):
        __tablename__ = 'hypergraphs'
        name = sa.Column(sa.String, primary_key=True)
        data = sa.Column(sa.LargeBinary)
        created_at = sa.Column(sa.DateTime)

    class AnalysisTable(Base):
        __tablename__ = 'analyses'
        name = sa.Column(sa.String, primary_key=True)
        data = sa.Column(sa.LargeBinary)
        created_at = sa.Column(sa.DateTime)

    class Layer1RegistryTable(Base):
        __tablename__ = 'layer1_registries'
        name = sa.Column(sa.String, primary_key=True)
        data = sa.Column(sa.LargeBinary)
        created_at = sa.Column(sa.DateTime)

    class PostgreSQLBackend(DatabaseBackend):
        """PostgreSQL backend using SQLAlchemy (async)."""

        def __init__(self, dsn: str):
            self.dsn = dsn
            self.engine = None
            self.async_session = None

        async def connect(self):
            self.engine = create_async_engine(self.dsn, echo=False)
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        async def close(self):
            if self.engine:
                await self.engine.dispose()

        async def store_relation(self, relation):
            data = pickle.dumps(relation)
            async with self.async_session() as session:
                async with session.begin():
                    stmt = sa.insert(RelationTable).values(
                        id=relation.id, data=data, created_at=datetime.utcnow()
                    ).on_conflict_do_update(
                        index_elements=['id'],
                        set_=dict(data=data, created_at=datetime.utcnow())
                    )
                    await session.execute(stmt)

        async def load_relation(self, relation_id):
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(RelationTable).where(RelationTable.id == relation_id)
                )
                row = result.scalar_one_or_none()
                if row:
                    return pickle.loads(row.data)
                return None

        async def store_hypergraph(self, hypergraph, name):
            data = pickle.dumps(hypergraph)
            async with self.async_session() as session:
                async with session.begin():
                    stmt = sa.insert(HypergraphTable).values(
                        name=name, data=data, created_at=datetime.utcnow()
                    ).on_conflict_do_update(
                        index_elements=['name'],
                        set_=dict(data=data, created_at=datetime.utcnow())
                    )
                    await session.execute(stmt)

        async def load_hypergraph(self, name):
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(HypergraphTable).where(HypergraphTable.name == name)
                )
                row = result.scalar_one_or_none()
                if row:
                    return pickle.loads(row.data)
                return None

        async def store_analysis(self, analysis, name):
            data = pickle.dumps(analysis)
            async with self.async_session() as session:
                async with session.begin():
                    stmt = sa.insert(AnalysisTable).values(
                        name=name, data=data, created_at=datetime.utcnow()
                    ).on_conflict_do_update(
                        index_elements=['name'],
                        set_=dict(data=data, created_at=datetime.utcnow())
                    )
                    await session.execute(stmt)

        async def load_analysis(self, name):
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(AnalysisTable).where(AnalysisTable.name == name)
                )
                row = result.scalar_one_or_none()
                if row:
                    return pickle.loads(row.data)
                return None

        # New methods for Layer 1 registries
        async def save_layer1_registry(self, registry, name):
            data = pickle.dumps(registry)
            async with self.async_session() as session:
                async with session.begin():
                    stmt = sa.insert(Layer1RegistryTable).values(
                        name=name, data=data, created_at=datetime.utcnow()
                    ).on_conflict_do_update(
                        index_elements=['name'],
                        set_=dict(data=data, created_at=datetime.utcnow())
                    )
                    await session.execute(stmt)

        async def load_layer1_registry(self, name):
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(Layer1RegistryTable).where(Layer1RegistryTable.name == name)
                )
                row = result.scalar_one_or_none()
                if row:
                    return pickle.loads(row.data)
                return None

        # Batch operations
        async def store_relations(self, relations):
            async with self.async_session() as session:
                async with session.begin():
                    now = datetime.utcnow()
                    for rel in relations:
                        stmt = sa.insert(RelationTable).values(
                            id=rel.id, data=pickle.dumps(rel), created_at=now
                        ).on_conflict_do_update(
                            index_elements=['id'],
                            set_=dict(data=pickle.dumps(rel), created_at=now)
                        )
                        await session.execute(stmt)

        async def load_relations(self, relation_ids):
            if not relation_ids:
                return []
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(RelationTable.id, RelationTable.data).where(
                        RelationTable.id.in_(relation_ids)
                    )
                )
                rows = result.all()
                data_map = {row.id: row.data for row in rows}
                result_list = []
                for rid in relation_ids:
                    data = data_map.get(rid)
                    result_list.append(pickle.loads(data) if data else None)
                return result_list

        async def store_hypergraphs(self, hypergraphs):
            async with self.async_session() as session:
                async with session.begin():
                    now = datetime.utcnow()
                    for name, hg in hypergraphs.items():
                        stmt = sa.insert(HypergraphTable).values(
                            name=name, data=pickle.dumps(hg), created_at=now
                        ).on_conflict_do_update(
                            index_elements=['name'],
                            set_=dict(data=pickle.dumps(hg), created_at=now)
                        )
                        await session.execute(stmt)

        async def load_hypergraphs(self, names):
            if not names:
                return []
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(HypergraphTable.name, HypergraphTable.data).where(
                        HypergraphTable.name.in_(names)
                    )
                )
                rows = result.all()
                data_map = {row.name: row.data for row in rows}
                result_list = []
                for name in names:
                    data = data_map.get(name)
                    result_list.append(pickle.loads(data) if data else None)
                return result_list

        async def store_analyses(self, analyses):
            async with self.async_session() as session:
                async with session.begin():
                    now = datetime.utcnow()
                    for name, an in analyses.items():
                        stmt = sa.insert(AnalysisTable).values(
                            name=name, data=pickle.dumps(an), created_at=now
                        ).on_conflict_do_update(
                            index_elements=['name'],
                            set_=dict(data=pickle.dumps(an), created_at=now)
                        )
                        await session.execute(stmt)

        async def load_analyses(self, names):
            if not names:
                return []
            async with self.async_session() as session:
                result = await session.execute(
                    sa.select(AnalysisTable.name, AnalysisTable.data).where(
                        AnalysisTable.name.in_(names)
                    )
                )
                rows = result.all()
                data_map = {row.name: row.data for row in rows}
                result_list = []
                for name in names:
                    data = data_map.get(name)
                    result_list.append(pickle.loads(data) if data else None)
                return result_list

else:
    class PostgreSQLBackend(DatabaseBackend):
        def __init__(self, *args, **kwargs):
            raise ImportError("SQLAlchemy is required for PostgreSQL backend")


# ============================================================================
# NEO4J BACKEND (with batch support)
# ============================================================================

if HAS_NEO4J:
    class Neo4jBackend(DatabaseBackend):
        """Neo4j graph database backend using the official async driver."""

        def __init__(self, uri: str, user: str, password: str):
            self.uri = uri
            self.user = user
            self.password = password
            self.driver = None

        async def connect(self):
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))

        async def close(self):
            if self.driver:
                await self.driver.close()

        async def store_relation(self, relation):
            data = relation.to_dict()
            async with self.driver.session() as session:
                await session.run(
                    "MERGE (r:Relation {id: $id}) SET r.data = $data, r.updated = datetime()",
                    id=relation.id,
                    data=json.dumps(data, cls=NumpyEncoder)
                )

        async def load_relation(self, relation_id):
            async with self.driver.session() as session:
                result = await session.run(
                    "MATCH (r:Relation {id: $id}) RETURN r.data AS data",
                    id=relation_id
                )
                record = await result.single()
                if record:
                    data = json.loads(record["data"], object_hook=decode_numpy)
                    from .relations import UltimateRelation
                    return UltimateRelation.from_dict(data)
                return None

        async def store_hypergraph(self, hypergraph, name):
            data = hypergraph.to_dict()
            async with self.driver.session() as session:
                await session.run(
                    "MERGE (h:Hypergraph {name: $name}) SET h.data = $data, h.updated = datetime()",
                    name=name,
                    data=json.dumps(data, cls=NumpyEncoder)
                )

        async def load_hypergraph(self, name):
            async with self.driver.session() as session:
                result = await session.run(
                    "MATCH (h:Hypergraph {name: $name}) RETURN h.data AS data",
                    name=name
                )
                record = await result.single()
                if record:
                    data = json.loads(record["data"], object_hook=decode_numpy)
                    from .hypergraph_relations import Hypergraph
                    return Hypergraph.from_dict(data)
                return None

        async def store_analysis(self, analysis, name):
            data = analysis.to_dict()
            async with self.driver.session() as session:
                await session.run(
                    "MERGE (a:Analysis {name: $name}) SET a.data = $data, a.updated = datetime()",
                    name=name,
                    data=json.dumps(data, cls=NumpyEncoder)
                )

        async def load_analysis(self, name):
            async with self.driver.session() as session:
                result = await session.run(
                    "MATCH (a:Analysis {name: $name}) RETURN a.data AS data",
                    name=name
                )
                record = await result.single()
                if record:
                    data = json.loads(record["data"], object_hook=decode_numpy)
                    from .motif_detection import TopologicalNetworkAnalysis
                    return TopologicalNetworkAnalysis.from_dict(data)
                return None

        # New method for resonance graph
        async def save_resonance_graph(self, graph, name: str):
            """
            Store a resonance graph under the given name.
            The graph can be a NetworkX graph, an object with a to_dict() method, or a plain dictionary.
            It is serialized to JSON and stored as a node with label `ResonanceGraph`.
            """
            if HAS_NETWORKX and isinstance(graph, nx.Graph):
                data = nx.node_link_data(graph)
            elif hasattr(graph, 'to_dict'):
                data = graph.to_dict()
            else:
                # Assume graph is already a dict-like object
                data = graph
            async with self.driver.session() as session:
                await session.run(
                    "MERGE (r:ResonanceGraph {name: $name}) SET r.data = $data, r.updated = datetime()",
                    name=name,
                    data=json.dumps(data, cls=NumpyEncoder)
                )

        # New methods for Layer 1 registries (using JSON serialization)
        async def save_layer1_registry(self, registry, name):
            async with self.driver.session() as session:
                await session.run(
                    "MERGE (r:Layer1Registry {name: $name}) SET r.data = $data, r.updated = datetime()",
                    name=name,
                    data=json.dumps(registry, cls=NumpyEncoder)
                )

        async def load_layer1_registry(self, name):
            async with self.driver.session() as session:
                result = await session.run(
                    "MATCH (r:Layer1Registry {name: $name}) RETURN r.data AS data",
                    name=name
                )
                record = await result.single()
                if record:
                    return json.loads(record["data"], object_hook=decode_numpy)
                return None

        # Batch operations
        async def store_relations(self, relations):
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    for rel in relations:
                        data = rel.to_dict()
                        await tx.run(
                            "MERGE (r:Relation {id: $id}) SET r.data = $data, r.updated = datetime()",
                            id=rel.id,
                            data=json.dumps(data, cls=NumpyEncoder)
                        )

        async def load_relations(self, relation_ids):
            if not relation_ids:
                return []
            # Use UNWIND to load multiple in one query
            async with self.driver.session() as session:
                result = await session.run(
                    "UNWIND $ids AS id MATCH (r:Relation {id: id}) RETURN id, r.data AS data",
                    ids=relation_ids
                )
                records = await result.data()
                data_map = {rec['id']: rec['data'] for rec in records}
                result_list = []
                for rid in relation_ids:
                    data = data_map.get(rid)
                    if data:
                        obj_dict = json.loads(data, object_hook=decode_numpy)
                        from .relations import UltimateRelation
                        result_list.append(UltimateRelation.from_dict(obj_dict))
                    else:
                        result_list.append(None)
                return result_list

        async def store_hypergraphs(self, hypergraphs):
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    for name, hg in hypergraphs.items():
                        data = hg.to_dict()
                        await tx.run(
                            "MERGE (h:Hypergraph {name: $name}) SET h.data = $data, h.updated = datetime()",
                            name=name,
                            data=json.dumps(data, cls=NumpyEncoder)
                        )

        async def load_hypergraphs(self, names):
            if not names:
                return []
            async with self.driver.session() as session:
                result = await session.run(
                    "UNWIND $names AS name MATCH (h:Hypergraph {name: name}) RETURN name, h.data AS data",
                    names=names
                )
                records = await result.data()
                data_map = {rec['name']: rec['data'] for rec in records}
                result_list = []
                for name in names:
                    data = data_map.get(name)
                    if data:
                        obj_dict = json.loads(data, object_hook=decode_numpy)
                        from .hypergraph_relations import Hypergraph
                        result_list.append(Hypergraph.from_dict(obj_dict))
                    else:
                        result_list.append(None)
                return result_list

        async def store_analyses(self, analyses):
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    for name, an in analyses.items():
                        data = an.to_dict()
                        await tx.run(
                            "MERGE (a:Analysis {name: $name}) SET a.data = $data, a.updated = datetime()",
                            name=name,
                            data=json.dumps(data, cls=NumpyEncoder)
                        )

        async def load_analyses(self, names):
            if not names:
                return []
            async with self.driver.session() as session:
                result = await session.run(
                    "UNWIND $names AS name MATCH (a:Analysis {name: name}) RETURN name, a.data AS data",
                    names=names
                )
                records = await result.data()
                data_map = {rec['name']: rec['data'] for rec in records}
                result_list = []
                for name in names:
                    data = data_map.get(name)
                    if data:
                        obj_dict = json.loads(data, object_hook=decode_numpy)
                        from .motif_detection import TopologicalNetworkAnalysis
                        result_list.append(TopologicalNetworkAnalysis.from_dict(obj_dict))
                    else:
                        result_list.append(None)
                return result_list

else:
    class Neo4jBackend(DatabaseBackend):
        def __init__(self, *args, **kwargs):
            raise ImportError("Neo4j driver is required for Neo4j backend")


# ============================================================================
# MONGODB BACKEND (with batch support)
# ============================================================================

if HAS_MONGO:
    class MongoBackend(DatabaseBackend):
        """MongoDB backend using Motor (async)."""

        def __init__(self, connection_string: str, database: str = "layer2"):
            self.connection_string = connection_string
            self.database_name = database
            self.client = None
            self.db = None

        async def connect(self):
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]

        async def close(self):
            if self.client:
                self.client.close()

        async def store_relation(self, relation):
            data = relation.to_dict()
            data['_id'] = relation.id
            data['created_at'] = datetime.utcnow()
            await self.db.relations.replace_one(
                {'_id': relation.id},
                data,
                upsert=True
            )

        async def load_relation(self, relation_id):
            doc = await self.db.relations.find_one({'_id': relation_id})
            if doc:
                doc.pop('_id')
                from .relations import UltimateRelation
                return UltimateRelation.from_dict(doc)
            return None

        async def store_hypergraph(self, hypergraph, name):
            data = hypergraph.to_dict()
            data['_id'] = name
            data['created_at'] = datetime.utcnow()
            await self.db.hypergraphs.replace_one(
                {'_id': name},
                data,
                upsert=True
            )

        async def load_hypergraph(self, name):
            doc = await self.db.hypergraphs.find_one({'_id': name})
            if doc:
                doc.pop('_id')
                from .hypergraph_relations import Hypergraph
                return Hypergraph.from_dict(doc)
            return None

        async def store_analysis(self, analysis, name):
            data = analysis.to_dict()
            data['_id'] = name
            data['created_at'] = datetime.utcnow()
            await self.db.analyses.replace_one(
                {'_id': name},
                data,
                upsert=True
            )

        async def load_analysis(self, name):
            doc = await self.db.analyses.find_one({'_id': name})
            if doc:
                doc.pop('_id')
                from .motif_detection import TopologicalNetworkAnalysis
                return TopologicalNetworkAnalysis.from_dict(doc)
            return None

        # New methods for Layer 1 registries
        async def save_layer1_registry(self, registry, name):
            data = registry.copy()
            data['_id'] = name
            data['created_at'] = datetime.utcnow()
            await self.db.layer1_registries.replace_one(
                {'_id': name},
                data,
                upsert=True
            )

        async def load_layer1_registry(self, name):
            doc = await self.db.layer1_registries.find_one({'_id': name})
            if doc:
                doc.pop('_id')
                doc.pop('created_at', None)
                return doc
            return None

        # Batch operations
        async def store_relations(self, relations):
            operations = []
            now = datetime.utcnow()
            for rel in relations:
                data = rel.to_dict()
                data['_id'] = rel.id
                data['created_at'] = now
                operations.append(
                    pymongo.ReplaceOne({'_id': rel.id}, data, upsert=True)
                )
            if operations:
                await self.db.relations.bulk_write(operations)

        async def load_relations(self, relation_ids):
            if not relation_ids:
                return []
            cursor = self.db.relations.find({'_id': {'$in': relation_ids}})
            docs = await cursor.to_list(length=None)
            data_map = {doc['_id']: doc for doc in docs}
            result = []
            for rid in relation_ids:
                doc = data_map.get(rid)
                if doc:
                    doc_copy = doc.copy()
                    doc_copy.pop('_id')
                    from .relations import UltimateRelation
                    result.append(UltimateRelation.from_dict(doc_copy))
                else:
                    result.append(None)
            return result

        async def store_hypergraphs(self, hypergraphs):
            operations = []
            now = datetime.utcnow()
            for name, hg in hypergraphs.items():
                data = hg.to_dict()
                data['_id'] = name
                data['created_at'] = now
                operations.append(
                    pymongo.ReplaceOne({'_id': name}, data, upsert=True)
                )
            if operations:
                await self.db.hypergraphs.bulk_write(operations)

        async def load_hypergraphs(self, names):
            if not names:
                return []
            cursor = self.db.hypergraphs.find({'_id': {'$in': names}})
            docs = await cursor.to_list(length=None)
            data_map = {doc['_id']: doc for doc in docs}
            result = []
            for name in names:
                doc = data_map.get(name)
                if doc:
                    doc_copy = doc.copy()
                    doc_copy.pop('_id')
                    from .hypergraph_relations import Hypergraph
                    result.append(Hypergraph.from_dict(doc_copy))
                else:
                    result.append(None)
            return result

        async def store_analyses(self, analyses):
            operations = []
            now = datetime.utcnow()
            for name, an in analyses.items():
                data = an.to_dict()
                data['_id'] = name
                data['created_at'] = now
                operations.append(
                    pymongo.ReplaceOne({'_id': name}, data, upsert=True)
                )
            if operations:
                await self.db.analyses.bulk_write(operations)

        async def load_analyses(self, names):
            if not names:
                return []
            cursor = self.db.analyses.find({'_id': {'$in': names}})
            docs = await cursor.to_list(length=None)
            data_map = {doc['_id']: doc for doc in docs}
            result = []
            for name in names:
                doc = data_map.get(name)
                if doc:
                    doc_copy = doc.copy()
                    doc_copy.pop('_id')
                    from .motif_detection import TopologicalNetworkAnalysis
                    result.append(TopologicalNetworkAnalysis.from_dict(doc_copy))
                else:
                    result.append(None)
            return result

else:
    class MongoBackend(DatabaseBackend):
        def __init__(self, *args, **kwargs):
            raise ImportError("MongoDB driver (motor) is required for MongoDB backend")


# ============================================================================
# REDIS BACKEND (as a storage backend, not cache)
# ============================================================================

if HAS_REDIS:
    class RedisBackend(DatabaseBackend):
        """
        Redis backend using redis.asyncio.
        Stores objects as pickled values under prefixed keys.
        """

        def __init__(self, url: str = "redis://localhost:6379", prefix: str = "layer2:"):
            self.url = url
            self.prefix = prefix
            self.client = None

        async def connect(self):
            self.client = redis.from_url(self.url, decode_responses=False)

        async def close(self):
            if self.client:
                await self.client.close()

        def _key(self, kind: str, identifier: str) -> str:
            return f"{self.prefix}{kind}:{identifier}"

        async def store_relation(self, relation):
            key = self._key("relation", relation.id)
            await self.client.set(key, pickle.dumps(relation))

        async def load_relation(self, relation_id):
            key = self._key("relation", relation_id)
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
            return None

        async def store_hypergraph(self, hypergraph, name):
            key = self._key("hypergraph", name)
            await self.client.set(key, pickle.dumps(hypergraph))

        async def load_hypergraph(self, name):
            key = self._key("hypergraph", name)
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
            return None

        async def store_analysis(self, analysis, name):
            key = self._key("analysis", name)
            await self.client.set(key, pickle.dumps(analysis))

        async def load_analysis(self, name):
            key = self._key("analysis", name)
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
            return None

        # New methods for Layer 1 registries
        async def save_layer1_registry(self, registry, name):
            key = self._key("layer1", name)
            await self.client.set(key, pickle.dumps(registry))

        async def load_layer1_registry(self, name):
            key = self._key("layer1", name)
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
            return None

        # Batch operations using pipelines
        async def store_relations(self, relations):
            async with self.client.pipeline() as pipe:
                for rel in relations:
                    key = self._key("relation", rel.id)
                    await pipe.set(key, pickle.dumps(rel))
                await pipe.execute()

        async def load_relations(self, relation_ids):
            if not relation_ids:
                return []
            keys = [self._key("relation", rid) for rid in relation_ids]
            data_list = await self.client.mget(*keys)
            result = []
            for data in data_list:
                if data:
                    result.append(pickle.loads(data))
                else:
                    result.append(None)
            return result

        async def store_hypergraphs(self, hypergraphs):
            async with self.client.pipeline() as pipe:
                for name, hg in hypergraphs.items():
                    key = self._key("hypergraph", name)
                    await pipe.set(key, pickle.dumps(hg))
                await pipe.execute()

        async def load_hypergraphs(self, names):
            if not names:
                return []
            keys = [self._key("hypergraph", name) for name in names]
            data_list = await self.client.mget(*keys)
            result = []
            for data in data_list:
                if data:
                    result.append(pickle.loads(data))
                else:
                    result.append(None)
            return result

        async def store_analyses(self, analyses):
            async with self.client.pipeline() as pipe:
                for name, an in analyses.items():
                    key = self._key("analysis", name)
                    await pipe.set(key, pickle.dumps(an))
                await pipe.execute()

        async def load_analyses(self, names):
            if not names:
                return []
            keys = [self._key("analysis", name) for name in names]
            data_list = await self.client.mget(*keys)
            result = []
            for data in data_list:
                if data:
                    result.append(pickle.loads(data))
                else:
                    result.append(None)
            return result

else:
    class RedisBackend(DatabaseBackend):
        def __init__(self, *args, **kwargs):
            raise ImportError("Redis driver (redis.asyncio) is required for Redis backend")


# ============================================================================
# DATABASE MANAGER (HIGH‑LEVEL INTERFACE) with caching
# ============================================================================

class DatabaseManager:
    """
    High‑level manager for database operations.
    Supports multiple backends and provides a unified async interface.
    Optionally uses a cache backend (e.g., Redis) to speed up reads.
    """

    def __init__(self, backend: DatabaseBackend, cache: Optional[CacheBackend] = None):
        """
        Args:
            backend: An instance of a DatabaseBackend subclass.
            cache: Optional cache backend (e.g., RedisCache) for read caching.
        """
        self.backend = backend
        self.cache = cache
        self._cache_ttl = 3600  # default 1 hour

    async def connect(self):
        await self.backend.connect()
        if self.cache and hasattr(self.cache, 'connect'):
            await self.cache.connect()

    async def close(self):
        await self.backend.close()
        if self.cache:
            await self.cache.close()

    # ------------------------------------------------------------------------
    # Single object methods (with caching)
    # ------------------------------------------------------------------------

    async def store_relation(self, relation):
        await self.backend.store_relation(relation)
        if self.cache:
            key = f"relation:{relation.id}"
            await self.cache.set(key, relation, ttl=self._cache_ttl)

    async def load_relation(self, relation_id: str):
        # Try cache first
        if self.cache:
            key = f"relation:{relation_id}"
            cached = await self.cache.get(key)
            if cached is not None:
                return cached
        # Fallback to backend
        obj = await self.backend.load_relation(relation_id)
        if obj and self.cache:
            await self.cache.set(key, obj, ttl=self._cache_ttl)
        return obj

    async def store_hypergraph(self, hypergraph, name: str):
        await self.backend.store_hypergraph(hypergraph, name)
        if self.cache:
            key = f"hypergraph:{name}"
            await self.cache.set(key, hypergraph, ttl=self._cache_ttl)

    async def load_hypergraph(self, name: str):
        if self.cache:
            key = f"hypergraph:{name}"
            cached = await self.cache.get(key)
            if cached is not None:
                return cached
        obj = await self.backend.load_hypergraph(name)
        if obj and self.cache:
            await self.cache.set(key, obj, ttl=self._cache_ttl)
        return obj

    async def store_analysis(self, analysis, name: str):
        await self.backend.store_analysis(analysis, name)
        if self.cache:
            key = f"analysis:{name}"
            await self.cache.set(key, analysis, ttl=self._cache_ttl)

    async def load_analysis(self, name: str):
        if self.cache:
            key = f"analysis:{name}"
            cached = await self.cache.get(key)
            if cached is not None:
                return cached
        obj = await self.backend.load_analysis(name)
        if obj and self.cache:
            await self.cache.set(key, obj, ttl=self._cache_ttl)
        return obj

    # New methods for Layer 1 registries (with caching)
    async def save_layer1_registry(self, registry, name: str):
        await self.backend.save_layer1_registry(registry, name)
        if self.cache:
            key = f"layer1:{name}"
            await self.cache.set(key, registry, ttl=self._cache_ttl)

    async def load_layer1_registry(self, name: str):
        if self.cache:
            key = f"layer1:{name}"
            cached = await self.cache.get(key)
            if cached is not None:
                return cached
        obj = await self.backend.load_layer1_registry(name)
        if obj and self.cache:
            await self.cache.set(key, obj, ttl=self._cache_ttl)
        return obj

    # ------------------------------------------------------------------------
    # Batch methods (with caching support)
    # ------------------------------------------------------------------------

    async def store_relations(self, relations: List):
        await self.backend.store_relations(relations)
        if self.cache:
            mapping = {f"relation:{r.id}": r for r in relations}
            await self.cache.mset(mapping, ttl=self._cache_ttl)

    async def load_relations(self, relation_ids: List[str]):
        if not relation_ids:
            return []
        # Try cache for all ids
        if self.cache:
            cache_keys = [f"relation:{rid}" for rid in relation_ids]
            cached_values = await self.cache.mget(cache_keys)
            # Build map of found cache entries
            found = {}
            missing_ids = []
            for idx, rid in enumerate(relation_ids):
                if cached_values[idx] is not None:
                    found[rid] = cached_values[idx]
                else:
                    missing_ids.append(rid)
            if not missing_ids:
                # All from cache
                return [found[rid] for rid in relation_ids]
            # Load missing from backend
            backend_objs = await self.backend.load_relations(missing_ids)
            # Combine results
            result = []
            cache_updates = {}
            for rid in relation_ids:
                if rid in found:
                    result.append(found[rid])
                else:
                    # find in backend_objs (order corresponds to missing_ids)
                    idx = missing_ids.index(rid)
                    obj = backend_objs[idx]
                    result.append(obj)
                    if obj is not None:
                        cache_updates[f"relation:{rid}"] = obj
            if cache_updates:
                await self.cache.mset(cache_updates, ttl=self._cache_ttl)
            return result
        else:
            # No cache, direct backend
            return await self.backend.load_relations(relation_ids)

    async def store_hypergraphs(self, hypergraphs: Dict[str, 'Hypergraph']):
        await self.backend.store_hypergraphs(hypergraphs)
        if self.cache:
            mapping = {f"hypergraph:{name}": hg for name, hg in hypergraphs.items()}
            await self.cache.mset(mapping, ttl=self._cache_ttl)

    async def load_hypergraphs(self, names: List[str]):
        if not names:
            return []
        if self.cache:
            cache_keys = [f"hypergraph:{name}" for name in names]
            cached_values = await self.cache.mget(cache_keys)
            found = {}
            missing = []
            for idx, name in enumerate(names):
                if cached_values[idx] is not None:
                    found[name] = cached_values[idx]
                else:
                    missing.append(name)
            if not missing:
                return [found[name] for name in names]
            backend_objs = await self.backend.load_hypergraphs(missing)
            result = []
            cache_updates = {}
            for name in names:
                if name in found:
                    result.append(found[name])
                else:
                    idx = missing.index(name)
                    obj = backend_objs[idx]
                    result.append(obj)
                    if obj is not None:
                        cache_updates[f"hypergraph:{name}"] = obj
            if cache_updates:
                await self.cache.mset(cache_updates, ttl=self._cache_ttl)
            return result
        else:
            return await self.backend.load_hypergraphs(names)

    async def store_analyses(self, analyses: Dict[str, 'TopologicalNetworkAnalysis']):
        await self.backend.store_analyses(analyses)
        if self.cache:
            mapping = {f"analysis:{name}": an for name, an in analyses.items()}
            await self.cache.mset(mapping, ttl=self._cache_ttl)

    async def load_analyses(self, names: List[str]):
        if not names:
            return []
        if self.cache:
            cache_keys = [f"analysis:{name}" for name in names]
            cached_values = await self.cache.mget(cache_keys)
            found = {}
            missing = []
            for idx, name in enumerate(names):
                if cached_values[idx] is not None:
                    found[name] = cached_values[idx]
                else:
                    missing.append(name)
            if not missing:
                return [found[name] for name in names]
            backend_objs = await self.backend.load_analyses(missing)
            result = []
            cache_updates = {}
            for name in names:
                if name in found:
                    result.append(found[name])
                else:
                    idx = missing.index(name)
                    obj = backend_objs[idx]
                    result.append(obj)
                    if obj is not None:
                        cache_updates[f"analysis:{name}"] = obj
            if cache_updates:
                await self.cache.mset(cache_updates, ttl=self._cache_ttl)
            return result
        else:
            return await self.backend.load_analyses(names)

    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ============================================================================
# DEMO / TEST
# ============================================================================

async def demo():
    """Demonstrate storing and loading a relation using SQLite and optional Redis cache."""
    logging.basicConfig(level=logging.INFO)

    # Create a dummy relation (requires actual classes)
    from .relations import UltimateRelation, RelationType
    rel = UltimateRelation(
        id="rel123",
        source_id="obs1",
        target_id="obs2",
        relation_type=RelationType.SYMMETRIC,
        weight=0.75
    )

    # SQLite backend
    backend = SQLiteBackend(":memory:")

    # Optional Redis cache (if available)
    cache = None
    if HAS_REDIS:
        try:
            cache = RedisCache("redis://localhost:6379")
            await cache.connect()  # will be connected by manager
        except Exception as e:
            logger.warning("Redis not available, proceeding without cache: %s", e)

    manager = DatabaseManager(backend, cache=cache)

    async with manager:
        await manager.store_relation(rel)
        loaded = await manager.load_relation("rel123")
        print(f"Loaded relation: {loaded.id} with weight {loaded.weight}")

        # Test Layer 1 registry
        test_registry = {'observables': {'temp': [20.5, 21.0, 22.1]}}
        await manager.save_layer1_registry(test_registry, "weather")
        loaded_reg = await manager.load_layer1_registry("weather")
        print(f"Loaded registry: {loaded_reg}")

    # Neo4j demo if available (commented out)
    # backend = Neo4jBackend("bolt://localhost:7687", "neo4j", "password")
    # manager = DatabaseManager(backend)
    # async with manager:
    #     await manager.store_relation(rel)
    #     loaded = await manager.load_relation("rel123")
    #     print(loaded)
    #     # Test resonance graph (requires networkx)
    #     if HAS_NETWORKX:
    #         G = nx.Graph()
    #         G.add_edge("A", "B", weight=0.9)
    #         await backend.save_resonance_graph(G, "test_resonance")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())