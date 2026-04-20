import numpy as np
import random
from collections import defaultdict

# ---------------------------
# 🔹 SEMANTIC ENCODER v3
# ---------------------------

class SemanticEncoder:
    def __init__(self, dim=12):
        self.dim = dim

    def encode(self, value):
        vec = np.zeros(self.dim)

        if isinstance(value, (int, float)):
            vec[0] = value
            vec[1] = value ** 2
            vec[2] = np.sin(value)
        elif isinstance(value, str):
            vec[0] = len(value)
            vec[1] = sum(ord(c) for c in value) % 1000
            vec[2] = vec[1] % 7
        else:
            vec[0] = 0

        return vec / (np.linalg.norm(vec) + 1e-6)


# ---------------------------
# 🔹 CONCEPT FORMATION
# ---------------------------

class ConceptLayer:
    def __init__(self):
        self.concepts = []

    def update(self, memory):
        if len(memory) < 5:
            return []

        data = np.array(memory)
        mean = np.mean(data, axis=0)

        # cluster-like abstraction
        concept = mean
        self.concepts.append(concept)

        return self.concepts


# ---------------------------
# 🔹 IDENTITY MODEL
# ---------------------------

class IdentityModel:
    def __init__(self):
        self.core = None

    def update(self, invariants, state):
        if len(invariants) == 0:
            return self.core

        stable_part = state[invariants]

        if self.core is None:
            self.core = stable_part
        else:
            self.core = 0.9 * self.core + 0.1 * stable_part

        return self.core


# ---------------------------
# 🔹 GOAL EVOLUTION
# ---------------------------

class GoalSystem:
    def __init__(self):
        self.goals = []

    def evolve(self, coherence, novelty, self_error):
        # spontaneous goal creation
        if coherence < 0.4:
            self.goals.append(("stabilize", 1.0))

        if novelty < 0.05:
            self.goals.append(("explore", 0.6))

        if self_error > 0.2:
            self.goals.append(("self_correct", 1.2))

    def select(self):
        if not self.goals:
            return None

        return max(self.goals, key=lambda x: x[1])[0]


# ---------------------------
# 🔹 WORLD MODEL v3
# ---------------------------

class WorldModel:
    def simulate(self, state, action):
        if action == "stabilize":
            return state * 0.9
        elif action == "explore":
            return state + np.random.normal(0, 0.1, size=state.shape)
        elif action == "self_correct":
            return state * 0.8 + np.mean(state)
        return state


# ---------------------------
# 🔹 COHERENCE FIELD
# ---------------------------

class CoherenceField:
    def __init__(self):
        self.states = []

    def update(self, state):
        self.states.append(state)

        if len(self.states) > 10:
            self.states.pop(0)

    def global_coherence(self):
        if len(self.states) < 2:
            return 0

        return 1 / (1 + np.var(self.states))


# ---------------------------
# 🔹 ENGINE v3
# ---------------------------

class CoherenceEngineV3:
    def __init__(self):
        self.encoder = SemanticEncoder()
        self.concepts = ConceptLayer()
        self.identity = IdentityModel()
        self.goals = GoalSystem()
        self.world = WorldModel()
        self.field = CoherenceField()

        self.memory = []
        self.state = None
        self.invariants = []

    # -----------------------
    def observe(self, input_data):
        emb = self.encoder.encode(input_data)

        if self.state is None:
            self.state = emb
        else:
            self.state = 0.6 * self.state + 0.4 * emb

        self.memory.append(self.state)
        self.field.update(self.state)

    # -----------------------
    def extract_invariants(self):
        if len(self.memory) < 4:
            return

        data = np.array(self.memory)
        var = np.var(data, axis=0)

        self.invariants = np.where(var < 0.02)[0]

    # -----------------------
    def coherence(self):
        return self.field.global_coherence()

    # -----------------------
    def novelty(self):
        if len(self.memory) < 2:
            return 0
        return np.linalg.norm(self.memory[-1] - self.memory[-2])

    # -----------------------
    def step(self, input_data):
        self.observe(input_data)

        self.extract_invariants()
        concepts = self.concepts.update(self.memory)

        coherence = self.coherence()
        novelty = self.novelty()

        identity = self.identity.update(self.invariants, self.state)

        self_error = np.linalg.norm(self.state - np.mean(self.memory))

        # evolve goals
        self.goals.evolve(coherence, novelty, self_error)
        action = self.goals.select()

        # simulate
        if action:
            self.state = self.world.simulate(self.state, action)

        return {
            "state": self.state,
            "coherence": coherence,
            "novelty": novelty,
            "identity": identity,
            "concepts": len(concepts),
            "action": action,
            "self_error": self_error,
            "invariants": self.invariants
        }


# ---------------------------
# 🔹 TEST
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngineV3()

    inputs = [10, 10.1, 10.2, 50, 10.05, 9.95, 10.0, 100, 10.1]

    for i, inp in enumerate(inputs):
        result = engine.step(inp)

        print(f"\nStep {i}")
        print("Input:", inp)
        print("Action:", result["action"])
        print("Coherence:", result["coherence"])
        print("Identity:", result["identity"])
        print("Concepts:", result["concepts"])
        print("Self-error:", result["self_error"])
        print("Invariants:", result["invariants"])
