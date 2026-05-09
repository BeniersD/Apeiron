import pytest
import asyncio
import os

# Deze test gebruikt alleen SQLite (altijd beschikbaar)
def test_sqlite_store_and_load():
    from apeiron.infrastructure.database import DatabaseManager, SQLiteBackend
    from apeiron.layers.layer02_relational.relations_core import UltimateRelation, RelationType

    backend = SQLiteBackend(":memory:")
    manager = DatabaseManager(backend)

    async def _run():
        await manager.connect()
        rel = UltimateRelation(
            id="test_rel", source_id="A", target_id="B",
            relation_type=RelationType.SYMMETRIC, weight=0.8
        )
        await manager.store_relation(rel)
        loaded = await manager.load_relation("test_rel")
        assert loaded is not None
        assert loaded.id == "test_rel"
        await manager.close()

    asyncio.run(_run())

# Voor Neo4j: alleen testen als het driver-pakket beschikbaar is
def test_neo4j_integration():
    """Test Neo4j backend – import en optionele verbindingstest."""
    pytest.importorskip("neo4j")
    from apeiron.infrastructure.database import Neo4jBackend, DatabaseManager
    from apeiron.layers.layer02_relational.relations_core import UltimateRelation, RelationType

    uri = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "test1234")

    async def _probe():
        backend = Neo4jBackend(uri, user, password)
        try:
            await backend.connect()
        except Exception as e:
            pytest.skip(f"Neo4j server not reachable: {e}")
        finally:
            await backend.close()

    # Eerst controleren of we verbinding kunnen maken
    asyncio.run(_probe())

    # Als we hier komen, is de server beschikbaar – volledige test uitvoeren
    backend = Neo4jBackend(uri, user, password)
    manager = DatabaseManager(backend)

    async def _run():
        await manager.connect()
        rel = UltimateRelation(
            id="test_neo_rel",
            source_id="X",
            target_id="Y",
            relation_type=RelationType.SYMMETRIC,
            weight=0.9,
        )
        await manager.store_relation(rel)
        loaded = await manager.load_relation("test_neo_rel")
        assert loaded is not None
        assert loaded.id == "test_neo_rel"
        await manager.close()

    asyncio.run(_run())