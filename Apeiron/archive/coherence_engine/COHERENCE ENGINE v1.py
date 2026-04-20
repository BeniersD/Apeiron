import numpy as np
from collections import defaultdict
import random

# ---------------------------
# 🔹 SEMANTIC ENCODING
# ---------------------------

def simple_embedding(value):
    """Convert input into vector space (placeholder semantic encoding)"""
    if isinstance(value, (int, float)):
        return np.array([value])
    elif isinstance(value, str):
        return np.array([sum(ord(c) for c in value) % 1000])
    elif isinstance(value, list):
        return np.array([len(value)])
    else:
        return np.array([0.0])


# ---------------------------
# 🔹 SELF MODEL
# ---------------------------

class SelfModel:
    def __init__(self):
        self.predicted_state = None
        self.identity = None

    def predict(self, state):
        if state is None:
            return None
        return state * 0.95  # naive prediction

    def update(self, actual_state):
        prediction = self.predict(actual_state)

        if prediction is None:
            return 0

        error = np.linalg.norm(actual_state - prediction)

        # identity = stable pattern
        self.identity = actual_state if error < 0.1 else self.identity

        return error


# ---------------------------
# 🔹 COHERENCE ENGINE
# ---------------------------

class CoherenceEngine:
    def __init__(self):
        self.state = None
        self.memory = []
        self.embeddings = []
        self.relations = defaultdict(float)
        self.invariants = []
        self.goals = []
        self.self_model = SelfModel()

    # -----------------------
    # OBSERVE
    # -----------------------
    def observe(self, input_data):
        emb = simple_embedding(input_data)

        self.embeddings.append(emb)

        if self.state is None:
            self.state = emb
        else:
            self.state = (self.state + emb) / 2

        self.memory.append(self.state)

    # -----------------------
    # RELATIONS (causal-ish)
    # -----------------------
    def update_relations(self):
        for i in range(len(self.embeddings) - 1):
            a = self.embeddings[i]
            b = self.embeddings[i + 1]

            diff = np.linalg.norm(a - b)
            strength = 1 / (1 + diff)

            self.relations[(i, i+1)] = strength

    # -----------------------
    # INVARIANTS
    # -----------------------
    def extract_invariants(self):
        if len(self.memory) < 2:
            return

        variances = np.var(self.memory, axis=0)

        self.invariants = np.where(variances < 0.05)[0]

    # -----------------------
    # COHERENCE
    # -----------------------
    def coherence(self):
        if len(self.invariants) == 0:
            return 0

        stable_values = [state[self.invariants] for state in self.memory]

        variance = np.var(stable_values)

        return 1 / (1 + variance)

    # -----------------------
    # GOALS (emergent)
    # -----------------------
    def update_goals(self):
        c = self.coherence()

        # low coherence → create stabilization goal
        if c < 0.5:
            self.goals.append("stabilize")

    # -----------------------
    # ACTION
    # -----------------------
    def act(self):
        if not self.goals:
            return None

        goal = self.goals[-1]

        if goal == "stabilize":
            noise = np.random.normal(0, 0.01, size=self.state.shape)
            self.state = self.state - noise  # reduce chaos

        return goal

    # -----------------------
    # REFLECT (self-awareness)
    # -----------------------
    def reflect(self):
        error = self.self_model.update(self.state)
        return error

    # -----------------------
    # STEP
    # -----------------------
    def step(self, input_data):
        self.observe(input_data)
        self.update_relations()
        self.extract_invariants()
        self.update_goals()

        action = self.act()
        coherence = self.coherence()
        self_error = self.reflect()

        return {
            "state": self.state,
            "coherence": coherence,
            "action": action,
            "self_error": self_error,
            "invariants": self.invariants
        }


# ---------------------------
# 🔹 TEST SIMULATION
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngine()

    inputs = [10, 11, 10.5, 10.2, 50, 10.1, 10.0]

    for i, inp in enumerate(inputs):
        result = engine.step(inp)

        print(f"\nStep {i}")
        print("Input:", inp)
        print("State:", result["state"])
        print("Coherence:", result["coherence"])
        print("Action:", result["action"])
        print("Self-error:", result["self_error"])
        print("Invariants:", result["invariants"])
