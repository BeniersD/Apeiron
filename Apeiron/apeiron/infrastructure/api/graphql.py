"""
GRAPHQL API
===========
This module provides a GraphQL API for Layer 2 (Relational Dynamics) and
Layer 1 (Observables) using Strawberry (preferred) or Graphene as fallback.
It allows querying and mutating observables and relations, and includes
subscriptions for real‑time updates (Strawberry only).

The API is designed to be integrated into a larger application (e.g., using
FastAPI or Starlette) and relies on the existing classes from layers 1 and 2.
All dependencies (layer instances) must be injected via the GraphQL context;
no global singletons are used.

Features:
- Queries for observables and relations with filtering and pagination.
- Mutations to create, update, and delete relations.
- Subscriptions (Strawberry) for real‑time notifications of mutations.
- Graceful degradation if required libraries are missing.
"""

import logging
import json
import asyncio
import enum
from typing import List, Optional, Dict, Any, AsyncGenerator, Set

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# Strawberry (modern GraphQL library for Python)
try:
    import strawberry
    from strawberry.fastapi import GraphQLRouter
    from strawberry.types import Info
    from strawberry.scalars import JSON
    HAS_STRAWBERRY = True
except ImportError:
    HAS_STRAWBERRY = False

# Graphene (fallback if Strawberry not available)
try:
    import graphene
    from graphene import ObjectType, String, Int, Float, Boolean, Field, List as GrapheneList, Mutation
    HAS_GRAPHENE = True
except ImportError:
    HAS_GRAPHENE = False

# If neither is installed, we raise an error only when trying to use the API.
if not (HAS_STRAWBERRY or HAS_GRAPHENE):
    raise ImportError("Either strawberry-graphql or graphene must be installed to use the GraphQL API.")

# Imports from layers (assuming correct relative paths)
from apeiron.layers.layer01_foundational.irreducible_unit import UltimateObservable, ObservabilityType
from apeiron.layers.layer01_foundational.observables import Layer1_Observables
from apeiron.layers.layer02_relational.relations_core import UltimateRelation, RelationType, Layer2_Relational_Ultimate

logger = logging.getLogger(__name__)


# ============================================================================
# EVENT BROADCASTER FOR SUBSCRIPTIONS
# ============================================================================

class Broadcaster:
    """
    Simple in‑memory pub/sub mechanism for GraphQL subscriptions.
    Each layer (or the GraphQL context) holds an instance.
    """
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    async def publish(self, event: Dict[str, Any]):
        """Send an event to all current subscribers."""
        for queue in list(self._subscribers):
            try:
                await queue.put(event)
            except Exception:
                # If a queue is closed, remove it
                self._subscribers.discard(queue)

    def subscribe(self) -> asyncio.Queue:
        """Create a new subscription queue."""
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Remove a subscription queue."""
        self._subscribers.discard(queue)


# ============================================================================
# HELPER FUNCTIONS – NO GLOBAL SINGLETONS ANYMORE
# ============================================================================

def get_layer1_from_context(info) -> Layer1_Observables:
    """Retrieve Layer1 instance from GraphQL context; raise if missing."""
    layer1 = info.context.get("layer1")
    if layer1 is None:
        raise RuntimeError("Layer1 instance not found in GraphQL context")
    return layer1


def get_layer2_from_context(info) -> Layer2_Relational_Ultimate:
    """Retrieve Layer2 instance from GraphQL context; raise if missing."""
    layer2 = info.context.get("layer2")
    if layer2 is None:
        raise RuntimeError("Layer2 instance not found in GraphQL context")
    return layer2


def get_broadcaster_from_context(info) -> Broadcaster:
    """Retrieve Broadcaster from GraphQL context; raise if missing."""
    broadcaster = info.context.get("broadcaster")
    if broadcaster is None:
        raise RuntimeError("Broadcaster not found in GraphQL context")
    return broadcaster


# ============================================================================
# STRAWBERRY IMPLEMENTATION (PREFERRED)
# ============================================================================

if HAS_STRAWBERRY:

    # ------------------------------------------------------------------------
    # GraphQL Types
    # ------------------------------------------------------------------------

    @strawberry.enum
    class GraphQLObservabilityType(enum.Enum):
        DISCRETE = "discrete"
        CONTINUOUS = "continuous"
        QUANTUM = "quantum"
        RELATIONAL = "relational"
        FUZZY = "fuzzy"
        STOCHASTIC = "stochastic"
        FRACTAL = "fractal"
        TOPOLOGICAL = "topological"
        SYMPLECTIC = "symplectic"
        COMPLEX = "complex"

    @strawberry.enum
    class GraphQLRelationType(enum.Enum):
        SYMMETRIC = "symmetric"
        DIRECTED = "directed"
        BIDIRECTIONAL = "bidirectional"
        WEIGHTED = "weighted"
        FUZZY = "fuzzy"
        TEMPORAL = "temporal"
        CAUSAL = "causal"
        QUANTUM = "quantum"
        HYPER = "hyper"
        HETEROGENEOUS = "heterogeneous"
        PROBABILISTIC = "probabilistic"
        LOGICAL = "logical"
        ONTOLOGICAL = "ontological"

    @strawberry.type
    class Observable:
        id: str
        value: str  # string representation
        observability_type: GraphQLObservabilityType
        temporal_phase: float
        qualitative_dims: Optional[str] = strawberry.field(
            description="JSON string of qualitative dimensions"
        )
        created_at: float

        @classmethod
        def from_ultimate(cls, obs: UltimateObservable) -> "Observable":
            return cls(
                id=obs.id,
                value=str(obs.value),
                observability_type=GraphQLObservabilityType(obs.observability_type.value),
                temporal_phase=obs.temporal_phase,
                qualitative_dims=json.dumps(obs.qualitative_dims),
                created_at=obs.created_at,
            )

    @strawberry.type
    class Relation:
        id: str
        source_id: str
        target_id: str
        relation_type: GraphQLRelationType
        weight: float
        distance: float
        similarity: float
        probability: float
        created_at: float
        metadata: Optional[str] = strawberry.field(
            description="JSON string of metadata"
        )

        @classmethod
        def from_ultimate(cls, rel: UltimateRelation) -> "Relation":
            return cls(
                id=rel.id,
                source_id=rel.source_id,
                target_id=rel.target_id,
                relation_type=GraphQLRelationType(rel.relation_type.value),
                weight=rel.weight,
                distance=rel.distance,
                similarity=rel.similarity,
                probability=rel.probability,
                created_at=rel.created_at,
                metadata=json.dumps(rel.metadata),
            )

    # ------------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------------

    @strawberry.type
    class Query:
        @strawberry.field
        def observable(self, id: str, info: Info) -> Optional[Observable]:
            layer1 = get_layer1_from_context(info)
            obs = layer1.get_observable(id)
            if obs:
                return Observable.from_ultimate(obs)
            return None

        @strawberry.field
        def observables(
            self,
            info: Info,
            limit: int = 100,
            offset: int = 0,
            type_filter: Optional[GraphQLObservabilityType] = None,
        ) -> List[Observable]:
            layer1 = get_layer1_from_context(info)
            all_obs = layer1.get_observables()
            if type_filter:
                filtered = [
                    o for o in all_obs
                    if o.observability_type.value == type_filter.value
                ]
            else:
                filtered = all_obs
            return [Observable.from_ultimate(o) for o in filtered[offset:offset+limit]]

        @strawberry.field
        def relation(self, id: str, info: Info) -> Optional[Relation]:
            layer2 = get_layer2_from_context(info)
            rel = layer2.relations.get(id)
            if rel:
                return Relation.from_ultimate(rel)
            return None

        @strawberry.field
        def relations(
            self,
            info: Info,
            source_id: Optional[str] = None,
            target_id: Optional[str] = None,
            type_filter: Optional[GraphQLRelationType] = None,
            limit: int = 100,
            offset: int = 0,
        ) -> List[Relation]:
            layer2 = get_layer2_from_context(info)
            rels = list(layer2.relations.values())
            if source_id:
                rels = [r for r in rels if r.source_id == source_id]
            if target_id:
                rels = [r for r in rels if r.target_id == target_id]
            if type_filter:
                rels = [r for r in rels if r.relation_type.value == type_filter.value]
            return [Relation.from_ultimate(r) for r in rels[offset:offset+limit]]

        @strawberry.field
        def stats(self, info: Info) -> str:
            layer2 = get_layer2_from_context(info)
            return json.dumps(layer2.get_stats(), indent=2)

    # ------------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------------

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def create_relation(
            self,
            info: Info,
            source_id: str,
            target_id: str,
            relation_type: GraphQLRelationType,
            weight: float = 1.0,
            metadata: Optional[str] = None,
        ) -> Relation:
            layer2 = get_layer2_from_context(info)
            broadcaster = get_broadcaster_from_context(info)
            rel = layer2.create_relation(
                source_id=source_id,
                target_id=target_id,
                relation_type=RelationType(relation_type.value),
                weight=weight,
                metadata=json.loads(metadata) if metadata else {},
            )
            # Publish event for subscriptions
            await broadcaster.publish({
                "type": "RELATION_CREATED",
                "data": Relation.from_ultimate(rel).__dict__
            })
            return Relation.from_ultimate(rel)

        @strawberry.mutation
        async def update_relation(
            self,
            info: Info,
            id: str,
            weight: Optional[float] = None,
            metadata: Optional[str] = None,
        ) -> Optional[Relation]:
            layer2 = get_layer2_from_context(info)
            broadcaster = get_broadcaster_from_context(info)
            rel = layer2.relations.get(id)
            if not rel:
                return None
            if weight is not None:
                rel.weight = weight
            if metadata is not None:
                rel.metadata.update(json.loads(metadata))
            await broadcaster.publish({
                "type": "RELATION_UPDATED",
                "data": Relation.from_ultimate(rel).__dict__
            })
            return Relation.from_ultimate(rel)

        @strawberry.mutation
        async def delete_relation(self, info: Info, id: str) -> bool:
            layer2 = get_layer2_from_context(info)
            broadcaster = get_broadcaster_from_context(info)
            if id in layer2.relations:
                # Capture data before deletion
                rel_data = Relation.from_ultimate(layer2.relations[id]).__dict__
                del layer2.relations[id]
                await broadcaster.publish({
                    "type": "RELATION_DELETED",
                    "data": rel_data
                })
                return True
            return False

    # ------------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------------

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def relation_events(self, info: Info) -> AsyncGenerator[JSON, None]:
            """
            Subscribe to real‑time relation events (created, updated, deleted).
            Each event is a dict with keys 'type' and 'data'.
            """
            broadcaster = get_broadcaster_from_context(info)
            queue = broadcaster.subscribe()
            try:
                while True:
                    event = await queue.get()
                    yield event
            finally:
                broadcaster.unsubscribe(queue)

        @strawberry.subscription
        async def relation_created(self, info: Info) -> AsyncGenerator[Relation, None]:
            """Subscribe to relation creation events only."""
            broadcaster = get_broadcaster_from_context(info)
            queue = broadcaster.subscribe()
            try:
                while True:
                    event = await queue.get()
                    if event.get("type") == "RELATION_CREATED":
                        # Reconstruct Relation object from dict
                        # For simplicity we use the dict; a more robust solution would validate.
                        yield Relation(**event["data"])
            finally:
                broadcaster.unsubscribe(queue)

    # ------------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------------

    schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)

    def create_graphql_router(
        layer1: Layer1_Observables,
        layer2: Layer2_Relational_Ultimate,
        broadcaster: Optional[Broadcaster] = None
    ) -> GraphQLRouter:
        """Create a FastAPI router for the GraphQL endpoint with dependency injection."""
        if broadcaster is None:
            broadcaster = Broadcaster()

        async def get_context():
            return {"layer1": layer1, "layer2": layer2, "broadcaster": broadcaster}

        return GraphQLRouter(schema, context_getter=get_context)


# ============================================================================
# GRAPHENE IMPLEMENTATION (FALLBACK) – no subscriptions
# ============================================================================

elif HAS_GRAPHENE:

    # ------------------------------------------------------------------------
    # GraphQL Types
    # ------------------------------------------------------------------------

    class ObservableType(ObjectType):
        id = String(required=True)
        value = String(required=True)
        observability_type = String(required=True)
        temporal_phase = Float(required=True)
        qualitative_dims = String()
        created_at = Float(required=True)

        def resolve_qualitative_dims(self, info):
            return json.dumps(self.obs.qualitative_dims)

        @staticmethod
        def from_ultimate(obs):
            obj = ObservableType()
            obj.obs = obs
            obj.id = obs.id
            obj.value = str(obs.value)
            obj.observability_type = obs.observability_type.value
            obj.temporal_phase = obs.temporal_phase
            obj.created_at = obs.created_at
            return obj

    class RelationType(ObjectType):
        id = String(required=True)
        source_id = String(required=True)
        target_id = String(required=True)
        relation_type = String(required=True)
        weight = Float(required=True)
        distance = Float(required=True)
        similarity = Float(required=True)
        probability = Float(required=True)
        created_at = Float(required=True)
        metadata = String()

        def resolve_metadata(self, info):
            return json.dumps(self.rel.metadata)

        @staticmethod
        def from_ultimate(rel):
            obj = RelationType()
            obj.rel = rel
            obj.id = rel.id
            obj.source_id = rel.source_id
            obj.target_id = rel.target_id
            obj.relation_type = rel.relation_type.value
            obj.weight = rel.weight
            obj.distance = rel.distance
            obj.similarity = rel.similarity
            obj.probability = rel.probability
            obj.created_at = rel.created_at
            return obj

    # ------------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------------

    class Query(ObjectType):
        observable = Field(ObservableType, id=String(required=True))
        observables = GrapheneList(
            ObservableType,
            limit=Int(default_value=100),
            offset=Int(default_value=0),
            type_filter=String(),
        )
        relation = Field(RelationType, id=String(required=True))
        relations = GrapheneList(
            RelationType,
            source_id=String(),
            target_id=String(),
            type_filter=String(),
            limit=Int(default_value=100),
            offset=Int(default_value=0),
        )
        stats = String()

        def resolve_observable(self, info, id):
            layer1 = info.context.get("layer1")
            if layer1 is None:
                raise RuntimeError("Layer1 instance not found in GraphQL context")
            obs = layer1.get_observable(id)
            if obs:
                return ObservableType.from_ultimate(obs)
            return None

        def resolve_observables(self, info, limit, offset, type_filter=None):
            layer1 = info.context.get("layer1")
            if layer1 is None:
                raise RuntimeError("Layer1 instance not found in GraphQL context")
            all_obs = layer1.get_observables()
            if type_filter:
                filtered = [o for o in all_obs if o.observability_type.value == type_filter]
            else:
                filtered = all_obs
            sliced = filtered[offset:offset+limit]
            return [ObservableType.from_ultimate(o) for o in sliced]

        def resolve_relation(self, info, id):
            layer2 = info.context.get("layer2")
            if layer2 is None:
                raise RuntimeError("Layer2 instance not found in GraphQL context")
            rel = layer2.relations.get(id)
            if rel:
                return RelationType.from_ultimate(rel)
            return None

        def resolve_relations(self, info, source_id=None, target_id=None, type_filter=None, limit=100, offset=0):
            layer2 = info.context.get("layer2")
            if layer2 is None:
                raise RuntimeError("Layer2 instance not found in GraphQL context")
            rels = list(layer2.relations.values())
            if source_id:
                rels = [r for r in rels if r.source_id == source_id]
            if target_id:
                rels = [r for r in rels if r.target_id == target_id]
            if type_filter:
                rels = [r for r in rels if r.relation_type.value == type_filter]
            sliced = rels[offset:offset+limit]
            return [RelationType.from_ultimate(r) for r in sliced]

        def resolve_stats(self, info):
            layer2 = info.context.get("layer2")
            if layer2 is None:
                raise RuntimeError("Layer2 instance not found in GraphQL context")
            return json.dumps(layer2.get_stats())

    # ------------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------------

    class CreateRelation(Mutation):
        class Arguments:
            source_id = String(required=True)
            target_id = String(required=True)
            relation_type = String(required=True)
            weight = Float(default_value=1.0)
            metadata = String()

        Output = RelationType

        def mutate(self, info, source_id, target_id, relation_type, weight=1.0, metadata=None):
            layer2 = info.context.get("layer2")
            if layer2 is None:
                raise RuntimeError("Layer2 instance not found in GraphQL context")
            rel = layer2.create_relation(
                source_id=source_id,
                target_id=target_id,
                relation_type=RelationType(relation_type),
                weight=weight,
                metadata=json.loads(metadata) if metadata else {},
            )
            return RelationType.from_ultimate(rel)

    class UpdateRelation(Mutation):
        class Arguments:
            id = String(required=True)
            weight = Float()
            metadata = String()

        Output = RelationType

        def mutate(self, info, id, weight=None, metadata=None):
            layer2 = info.context.get("layer2")
            if layer2 is None:
                raise RuntimeError("Layer2 instance not found in GraphQL context")
            rel = layer2.relations.get(id)
            if not rel:
                return None
            if weight is not None:
                rel.weight = weight
            if metadata is not None:
                rel.metadata.update(json.loads(metadata))
            return RelationType.from_ultimate(rel)

    class DeleteRelation(Mutation):
        class Arguments:
            id = String(required=True)

        Output = Boolean

        def mutate(self, info, id):
            layer2 = info.context.get("layer2")
            if layer2 is None:
                raise RuntimeError("Layer2 instance not found in GraphQL context")
            if id in layer2.relations:
                del layer2.relations[id]
                return True
            return False

    class Mutation(ObjectType):
        create_relation = CreateRelation.Field()
        update_relation = UpdateRelation.Field()
        delete_relation = DeleteRelation.Field()

    # ------------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------------

    schema = graphene.Schema(query=Query, mutation=Mutation)

    # Note: Graphene does not support subscriptions out of the box.
    # A note is added in the docstring.

    def create_graphql_app(layer1, layer2):
        """
        Returns a callable that can be mounted as a GraphQL endpoint in a
        ASGI/WSGI app. This is a simplified version; in practice you might use
        `graphene_fastapi.GraphQLApp`.
        """
        from graphql import graphql_sync
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        async def graphql_endpoint(request: Request):
            body = await request.json()
            query = body.get('query')
            variables = body.get('variables')
            context = {"layer1": layer1, "layer2": layer2}
            result = await graphql_sync(schema, query, context_value=context, variable_values=variables)
            return JSONResponse(result)

        return graphql_endpoint


# ============================================================================
# COMMON: Main entry point for running the server (optional)
# ============================================================================

def run_server(layer1=None, layer2=None, host="0.0.0.0", port=8000):
    """
    Run a standalone GraphQL server using uvicorn (if available) and the
    appropriate framework (FastAPI + Strawberry or Starlette + Graphene).
    """
    if layer1 is None:
        from apeiron.layers.layer01_foundational.observables import Layer1_Observables
        layer1 = Layer1_Observables()
    if layer2 is None:
        from apeiron.layers.layer02_relational.relations_core import Layer2_Relational_Ultimate
        layer2 = Layer2_Relational_Ultimate(layer1_registry=layer1.observables)

    if HAS_STRAWBERRY:
        from fastapi import FastAPI
        import uvicorn

        app = FastAPI()
        broadcaster = Broadcaster()
        router = create_graphql_router(layer1, layer2, broadcaster)
        app.include_router(router, prefix="/graphql")
        uvicorn.run(app, host=host, port=port)

    elif HAS_GRAPHENE:
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        graphql_endpoint = create_graphql_app(layer1, layer2)
        routes = [
            Route("/graphql", graphql_endpoint, methods=["POST"]),
        ]
        app = Starlette(routes=routes)
        uvicorn.run(app, host=host, port=port)

    else:
        logger.error("No GraphQL library available – cannot start server.")


# ============================================================================
# Demo (if run as main)
# ============================================================================

def demo():
    """Create dummy data and start a test server."""
    print("Starting demo GraphQL server on http://localhost:8000/graphql")
    print("Press Ctrl+C to stop.")

    # Create dummy layer1 and layer2 instances
    from apeiron.layers.layer01_foundational.observables import Layer1_Observables
    from apeiron.layers.layer02_relational.relations_core import Layer2_Relational_Ultimate

    l1 = Layer1_Observables()
    l2 = Layer2_Relational_Ultimate(layer1_registry=l1.observables)

    # Add some dummy observables
    obs1 = UltimateObservable(id="obs1", value=42, observability_type=ObservabilityType.DISCRETE)
    obs2 = UltimateObservable(id="obs2", value=3.14, observability_type=ObservabilityType.CONTINUOUS)
    l1.observables["obs1"] = obs1
    l1.observables["obs2"] = obs2

    # Add a relation
    l2.create_relation("obs1", "obs2", RelationType.SYMMETRIC, weight=0.8)

    run_server(l1, l2)


if __name__ == "__main__":
    demo()