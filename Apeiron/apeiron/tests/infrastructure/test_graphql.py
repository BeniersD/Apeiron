import pytest

def test_graphql_schema_loads():
    pytest.importorskip("strawberry")
    from apeiron.infrastructure.api.graphql import schema
    assert schema is not None

def test_graphql_router_creation():
    pytest.importorskip("strawberry")
    from apeiron.layers.layer02_relational.relations_core import Layer2_Relational_Ultimate
    from apeiron.infrastructure.api.graphql import create_graphql_router

    layer2 = Layer2_Relational_Ultimate()
    router = create_graphql_router(layer2, layer2)  # layer1 en layer2 hier hetzelfde voor test
    assert router is not None