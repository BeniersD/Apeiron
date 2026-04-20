import numpy as np
import random
from collections import defaultdict

# ---------------------------
# 🔹 SYMBOLIC LANGUAGE
# ---------------------------

class SymbolicLayer:
    def __init__(self):
        self.symbols = {}

    def assign(self, vector):
        key = tuple(np.round(vector, 2))

        if key not in self.symbols:
            self.symbols[key] = f"S{len(self.symbols)}"

        return self.symbols[key]


# ---------------------------
# 🔹 MULTI-SELF MODEL
# ---------------------------

class MultiSelfModel:
    def __init__(self):
        self.perspectives = []

    def update(self, state):
        # create slight variations = perspectives
        self.perspectives = [
            state,
            state * 0.9,
            state * 1.1
        ]

        return self.perspectives

    def conflict(self):
        if len(self.perspectives) < 2:
            return 0

        return np.var(self.perspectives)


# ---------------------------
# 🔹 GOAL ECOLOGY
# ---------------------------

class Goal:
    def __init__(self, name, energy):
        self.name = name
        self.energy = energy

    def decay(self):
        self.energy *= 0.95


class GoalEcology:
    def __init__(self):
        self.goals = []

    def update(self, coherence, novelty, conflict):
        if coherence < 0.4:
            self.goals.append(Goal("stabilize", 1.0))

        if novelty < 0.05:
            self.goals.append(Goal("explore", 0.7))

        if conflict > 0.1:
            self.goals.append(Goal("resolve_conflict", 1.2))

        for g in self.goals:
            g.decay()

        self.goals = [g for g in self.goals if g.energy > 0.1]

    def select(self):
        if not self.goals:
            return None

        return max(self.goals, key=lambda g: g.energy).name


# ---------------------------
# 🔹 WORLD SIMULATION v4
# ---------------------------

class WorldModel:
    def simulate(self, state, action):
        if action == "stabilize":
            return state * 0.9
        elif action == "explore":
            return state + np.random.normal(0, 0.1, size=state.shape)
        elif action == "resolve_conflict":
            return np.mean([state, state * 0.9, state * 1.1], axis=0)
        return state

    def rollout(self, state, action, steps=3):
        future = state.copy()

        for _ in range(steps):
            future = self.simulate(future, action)

        return future


# ---------------------------
# 🔹 MEANING LAYER
# ---------------------------

class MeaningLayer:
    def __init__(self):
        self.meanings = defaultdict(int)

    def update(self, symbol):
        self.meanings[symbol] += 1

    def significance(self, symbol):
        return self.meanings[symbol]


# ---------------------------
# 🔹 ENGINE v4
# ---------------------------

class CoherenceEngineV4:
    def __init__(self):
        self.state = None
        self.memory = []

        self.symbols = SymbolicLayer()
        self.self_model = MultiSelfModel()
        self.goals = GoalEcology()
        self.world = WorldModel()
        self.meaning = MeaningLayer()

    # -----------------------
    def encode(self, value):
        vec = np.array([
            value if isinstance(value, (int, float)) else 0,
            np.sin(value) if isinstance(value, (int, float)) else 0,
            np.cos(value) if isinstance(value, (int, float)) else 0
        ])

        return vec / (np.linalg.norm(vec) + 1e-6)

    # -----------------------
    def coherence(self):
        if len(self.memory) < 2:
            return 0
        return 1 / (1 + np.var(self.memory))

    def novelty(self):
        if len(self.memory) < 2:
            return 0
        return np.linalg.norm(self.memory[-1] - self.memory[-2])

    # -----------------------
    def step(self, input_data):
        emb = self.encode(input_data)

        if self.state is None:
            self.state = emb
        else:
            self.state = 0.5 * self.state + 0.5 * emb

        self.memory.append(self.state)

        # symbol grounding
        symbol = self.symbols.assign(self.state)
        self.meaning.update(symbol)

        # multi-self
        perspectives = self.self_model.update(self.state)
        conflict = self.self_model.conflict()

        # metrics
        coherence = self.coherence()
        novelty = self.novelty()

        # goals evolve
        self.goals.update(coherence, novelty, conflict)
        action = self.goals.select()

        # simulate multiple futures
        if action:
            future = self.world.rollout(self.state, action, steps=3)
            self.state = future

        return {
            "state": self.state,
            "symbol": symbol,
            "meaning": self.meaning.significance(symbol),
            "coherence": coherence,
            "novelty": novelty,
            "conflict": conflict,
            "action": action,
            "goals": [(g.name, round(g.energy, 2)) for g in self.goals.goals]
        }


# ---------------------------
# 🔹 TEST
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngineV4()

    inputs = [10, 10.1, 10.2, 50, 10.05, 10.0, 100, 9.9, 10.1]

    for i, inp in enumerate(inputs):
        result = engine.step(inp)

        print(f"\nStep {i}")
        print("Input:", inp)
        print("Symbol:", result["symbol"])
        print("Meaning strength:", result["meaning"])
        print("Action:", result["action"])
        print("Coherence:", result["coherence"])
        print("Conflict:", result["conflict"])
        print("Goals:", result["goals"])
