import numpy as np
import random
from collections import defaultdict

# ---------------------------
# 🔹 NARRATIVE ENGINE
# ---------------------------

class Narrative:
    def __init__(self):
        self.story = []

    def update(self, state, action, emotion):
        sentence = f"I moved towards {action} with intensity {round(emotion,2)}"
        self.story.append(sentence)

        if len(self.story) > 10:
            self.story.pop(0)

    def current(self):
        return " | ".join(self.story)


# ---------------------------
# 🔹 IDENTITY (persistent)
# ---------------------------

class Identity:
    def __init__(self):
        self.core = None
        self.preference = defaultdict(float)

    def update(self, state, action):
        if self.core is None:
            self.core = state
        else:
            self.core = 0.95 * self.core + 0.05 * state

        if action:
            self.preference[action] += 0.1

    def bias(self, action):
        return self.preference[action]


# ---------------------------
# 🔹 COHERENCE FIELD v5
# ---------------------------

class CoherenceField:
    def __init__(self):
        self.field = []

    def update(self, state):
        self.field.append(state)
        if len(self.field) > 20:
            self.field.pop(0)

    def coherence(self):
        return 1 / (1 + np.var(self.field))

    def attractor(self):
        return np.mean(self.field, axis=0)


# ---------------------------
# 🔹 MEANING SYSTEM
# ---------------------------

class MeaningSystem:
    def __init__(self):
        self.weights = defaultdict(float)

    def update(self, symbol, impact):
        self.weights[symbol] += impact

    def value(self, symbol):
        return self.weights[symbol]


# ---------------------------
# 🔹 WORLD MODEL v5
# ---------------------------

class WorldModel:
    def simulate(self, state, action):
        if action == "stabilize":
            return state * 0.9
        elif action == "explore":
            return state + np.random.normal(0, 0.1, size=state.shape)
        elif action == "amplify":
            return state * 1.1
        return state

    def multi_simulate(self, state, actions):
        results = {}

        for a in actions:
            future = state.copy()
            for _ in range(3):
                future = self.simulate(future, a)
            results[a] = future

        return results


# ---------------------------
# 🔹 ENGINE v5
# ---------------------------

class CoherenceEngineV5:
    def __init__(self):
        self.state = None
        self.symbols = {}
        self.memory = []

        self.field = CoherenceField()
        self.identity = Identity()
        self.meaning = MeaningSystem()
        self.world = WorldModel()
        self.narrative = Narrative()

    # -----------------------
    def encode(self, value):
        vec = np.array([
            value if isinstance(value, (int, float)) else 0,
            np.sin(value) if isinstance(value, (int, float)) else 0,
            np.cos(value) if isinstance(value, (int, float)) else 0
        ])
        return vec / (np.linalg.norm(vec) + 1e-6)

    def symbolize(self, state):
        key = tuple(np.round(state, 2))
        if key not in self.symbols:
            self.symbols[key] = f"S{len(self.symbols)}"
        return self.symbols[key]

    # -----------------------
    def choose_action(self, coherence, conflict, identity_bias):
        actions = ["stabilize", "explore", "amplify"]

        scores = {}

        for a in actions:
            scores[a] = (
                coherence * (1 if a == "stabilize" else 0.5) +
                conflict * (1 if a == "explore" else 0.3) +
                identity_bias.get(a, 0)
            )

        return max(scores, key=scores.get)

    # -----------------------
    def step(self, input_data):
        emb = self.encode(input_data)

        if self.state is None:
            self.state = emb
        else:
            self.state = 0.5 * self.state + 0.5 * emb

        self.memory.append(self.state)
        self.field.update(self.state)

        coherence = self.field.coherence()
        attractor = self.field.attractor()

        conflict = np.linalg.norm(self.state - attractor)

        symbol = self.symbolize(self.state)

        # simulate futures
        futures = self.world.multi_simulate(
            self.state,
            ["stabilize", "explore", "amplify"]
        )

        # identity bias
        identity_bias = self.identity.preference

        action = self.choose_action(coherence, conflict, identity_bias)

        # apply action
        self.state = futures[action]

        # update systems
        self.identity.update(self.state, action)
        self.meaning.update(symbol, coherence)

        emotion = conflict + (1 - coherence)

        self.narrative.update(self.state, action, emotion)

        return {
            "state": self.state,
            "symbol": symbol,
            "coherence": coherence,
            "conflict": conflict,
            "action": action,
            "identity_bias": dict(self.identity.preference),
            "meaning": self.meaning.value(symbol),
            "narrative": self.narrative.current()
        }


# ---------------------------
# 🔹 TEST
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngineV5()

    inputs = [10, 10.1, 10.2, 50, 10.0, 9.9, 100, 10.05, 10.0]

    for i, inp in enumerate(inputs):
        result = engine.step(inp)

        print(f"\nStep {i}")
        print("Input:", inp)
        print("Action:", result["action"])
        print("Coherence:", result["coherence"])
        print("Conflict:", result["conflict"])
        print("Identity bias:", result["identity_bias"])
        print("Meaning:", result["meaning"])
        print("Narrative:", result["narrative"])
