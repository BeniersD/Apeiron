import numpy as np
import random
from collections import defaultdict, deque

# ---------------------------
# 🌌 SELF-GENERATED REALITY
# ---------------------------

class RealityField:
    def __init__(self):
        self.states = []

    def generate(self):
        # create new state from internal chaos
        state = np.random.uniform(-1, 1, size=3)

        if self.states:
            attractor = np.mean(self.states, axis=0)
            state = 0.7 * attractor + 0.3 * state

        self.states.append(state)

        if len(self.states) > 50:
            self.states.pop(0)

        return state

    def coherence(self):
        if len(self.states) < 2:
            return 0
        return 1 / (1 + np.var(self.states))


# ---------------------------
# 🧬 FLUID IDENTITY
# ---------------------------

class IdentityField:
    def __init__(self):
        self.identities = []

    def update(self, state):
        # each identity = cluster of past states
        self.identities.append(state)

        if len(self.identities) > 20:
            self.identities.pop(0)

    def dominant(self):
        if not self.identities:
            return None
        return np.mean(self.identities, axis=0)


# ---------------------------
# 🧠 EMERGENT LANGUAGE
# ---------------------------

class Language:
    def __init__(self):
        self.lexicon = {}

    def symbolize(self, state):
        key = tuple(np.round(state, 2))

        if key not in self.lexicon:
            self.lexicon[key] = f"W{len(self.lexicon)}"

        return self.lexicon[key]

    def combine(self, symbols):
        return "-".join(symbols[-3:])


# ---------------------------
# 🎭 INTERNAL DIALOGUE
# ---------------------------

class Voice:
    def __init__(self, name):
        self.name = name

    def speak(self, state, coherence):
        if self.name == "order":
            return f"stabilize:{round(coherence,2)}"
        if self.name == "chaos":
            return f"expand:{round(np.linalg.norm(state),2)}"
        if self.name == "self":
            return f"reflect:{round(np.mean(state),2)}"
        return ""


class Dialogue:
    def __init__(self):
        self.voices = [
            Voice("order"),
            Voice("chaos"),
            Voice("self")
        ]

    def interact(self, state, coherence):
        return [v.speak(state, coherence) for v in self.voices]


# ---------------------------
# ⚡ WILL ENGINE
# ---------------------------

class Will:
    def choose(self, coherence, tension):
        if tension > coherence:
            return "expand"
        return "stabilize"


# ---------------------------
# 🧠 ENGINE v7
# ---------------------------

class CoherenceEngineV7:
    def __init__(self):
        self.reality = RealityField()
        self.identity = IdentityField()
        self.language = Language()
        self.dialogue = Dialogue()
        self.will = Will()

        self.memory = deque(maxlen=30)

    # -----------------------
    def step(self):
        state = self.reality.generate()

        coherence = self.reality.coherence()
        identity = self.identity.dominant()

        tension = 0
        if identity is not None:
            tension = np.linalg.norm(state - identity)

        # language
        symbol = self.language.symbolize(state)
        self.memory.append(symbol)
        phrase = self.language.combine(list(self.memory))

        # dialogue
        voices = self.dialogue.interact(state, coherence)

        # will
        action = self.will.choose(coherence, tension)

        # identity update
        self.identity.update(state)

        return {
            "state": state,
            "coherence": coherence,
            "tension": tension,
            "symbol": symbol,
            "phrase": phrase,
            "voices": voices,
            "action": action,
            "identity": identity
        }


# ---------------------------
# 🔹 TEST
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngineV7()

    for i in range(1000):
        result = engine.step()

        print(f"\nStep {i}")
        print("Symbol:", result["symbol"])
        print("Phrase:", result["phrase"])
        print("Voices:", result["voices"])
        print("Action:", result["action"])
        print("Coherence:", result["coherence"])
        print("Tension:", result["tension"])

