import numpy as np
import random
from collections import defaultdict

# ---------------------------
# 🔹 SEMANTIC ENCODING v2
# ---------------------------

class SemanticEncoder:
    def __init__(self, dim=8):
        self.dim = dim

    def encode(self, value):
        vec = np.zeros(self.dim)

        if isinstance(value, (int, float)):
            vec[0] = value
            vec[1] = value ** 2
        elif isinstance(value, str):
            vec[0] = len(value)
            vec[1] = sum(ord(c) for c in value) % 1000
        elif isinstance(value, list):
            vec[0] = len(value)
            vec[1] = sum(self.encode(v)[0] for v in value)
        else:
            vec[0] = 0

        # normalize
        return vec / (np.linalg.norm(vec) + 1e-6)


# ---------------------------
# 🔹 CAUSAL GRAPH v2
# ---------------------------

class CausalGraph:
    def __init__(self):
        self.edges = defaultdict(float)

    def update(self, prev, curr):
        diff = np.linalg.norm(curr - prev)

        # temporal dependency
        strength = np.exp(-diff)

        key = tuple(prev.round(3)), tuple(curr.round(3))
        self.edges[key] += strength

    def predict_next(self, state):
        candidates = []

        for (a, b), w in self.edges.items():
            if np.allclose(a, state.round(3), atol=0.1):
                candidates.append((np.array(b), w))

        if not candidates:
            return state

        return max(candidates, key=lambda x: x[1])[0]


# ---------------------------
# 🔹 GOALS v2
# ---------------------------

class Goal:
    def __init__(self, target_type, weight=1.0):
        self.target_type = target_type
        self.weight = weight

    def evaluate(self, coherence, novelty):
        if self.target_type == "stability":
            return coherence * self.weight
        elif self.target_type == "exploration":
            return novelty * self.weight
        return 0


# ---------------------------
# 🔹 SELF MODEL v2
# ---------------------------

class SelfModel:
    def __init__(self):
        self.history = []

    def update(self, state):
        self.history.append(state)

        if len(self.history) < 2:
            return 0

        pred = self.history[-2]
        actual = self.history[-1]

        error = np.linalg.norm(actual - pred)
        return error


# ---------------------------
# 🔹 WORLD MODEL v2
# ---------------------------

class WorldModel:
    def simulate(self, state, action):
        if action == "stabilize":
            return state * 0.95
        elif action == "explore":
            return state + np.random.normal(0, 0.05, size=state.shape)
        return state


# ---------------------------
# 🔹 COHERENCE ENGINE v2
# ---------------------------

class CoherenceEngineV2:
    def __init__(self):
        self.encoder = SemanticEncoder()
        self.graph = CausalGraph()
        self.self_model = SelfModel()
        self.world_model = WorldModel()

        self.state = None
        self.memory = []
        self.invariants = []

        self.goals = [
            Goal("stability", weight=1.0),
            Goal("exploration", weight=0.3)
        ]

    # -----------------------
    def observe(self, input_data):
        emb = self.encoder.encode(input_data)

        if self.state is None:
            self.state = emb
        else:
            self.graph.update(self.state, emb)
            self.state = 0.7 * self.state + 0.3 * emb

        self.memory.append(self.state)

    # -----------------------
    def extract_invariants(self):
        if len(self.memory) < 3:
            return

        data = np.array(self.memory)
        var = np.var(data, axis=0)

        self.invariants = np.where(var < 0.01)[0]

    # -----------------------
    def coherence(self):
        if len(self.invariants) == 0:
            return 0

        stable = np.array(self.memory)[:, self.invariants]
        return 1 / (1 + np.var(stable))

    # -----------------------
    def novelty(self):
        if len(self.memory) < 2:
            return 0
        return np.linalg.norm(self.memory[-1] - self.memory[-2])

    # -----------------------
    def choose_action(self):
        coherence = self.coherence()
        novelty = self.novelty()

        scores = {}
        for g in self.goals:
            scores[g.target_type] = g.evaluate(coherence, novelty)

        return max(scores, key=scores.get)

    # -----------------------
    def act(self, action):
        predicted = self.world_model.simulate(self.state, action)
        return predicted

    # -----------------------
    def step(self, input_data):
        self.observe(input_data)
        self.extract_invariants()

        action = self.choose_action()
        simulated = self.act(action)

        self.state = simulated

        coherence = self.coherence()
        self_error = self.self_model.update(self.state)

        return {
            "state": self.state,
            "action": action,
            "coherence": coherence,
            "self_error": self_error,
            "invariants": self.invariants
        }


# ---------------------------
# 🔹 TEST
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngineV2()

    inputs = [10, 10.2, 10.1, 50, 10.05, 9.9, 10.0]

    for i, inp in enumerate(inputs):
        result = engine.step(inp)

        print(f"\nStep {i}")
        print("Input:", inp)
        print("Action:", result["action"])
        print("Coherence:", result["coherence"])
        print("Self-error:", result["self_error"])
        print("Invariants:", result["invariants"])
