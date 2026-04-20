import numpy as np
import random
from collections import deque, defaultdict

# ---------------------------
# 🌍 ENVIRONMENT (1D world)
# ---------------------------

class Environment1D:
    def __init__(self, attractor=0.0):
        self.attractor = attractor

    def step(self, position, action):
        if action == "left":
            position -= 0.5
        elif action == "right":
            position += 0.5
        elif action == "stay":
            position += 0.0

        # reward = proximity to attractor (coherence with world)
        reward = 1 / (1 + abs(position - self.attractor))
        return position, reward


# ---------------------------
# 🧠 MEMORY
# ---------------------------

class Memory:
    def __init__(self, short=20, long=200):
        self.short = deque(maxlen=short)
        self.long = deque(maxlen=long)

    def add(self, experience):
        self.short.append(experience)
        self.long.append(experience)

    def recent_states(self):
        return [e["state"] for e in self.short]


# ---------------------------
# 🎭 INTERNAL VOICES
# ---------------------------

class Voice:
    def __init__(self, name, bias):
        self.name = name
        self.bias = bias  # preference weight

    def score(self, state, coherence, conflict, identity_bias):
        if self.name == "stabilizer":
            return coherence + identity_bias.get("stay", 0) + self.bias
        if self.name == "explorer":
            return conflict + identity_bias.get("right", 0) + self.bias
        if self.name == "amplifier":
            return np.linalg.norm(state) + identity_bias.get("left", 0) + self.bias
        return 0


class Dialogue:
    def __init__(self):
        self.voices = [
            Voice("stabilizer", 0.1),
            Voice("explorer", 0.1),
            Voice("amplifier", 0.1),
        ]

    def decide(self, state, coherence, conflict, identity_bias):
        scores = {}
        for v in self.voices:
            scores[v.name] = v.score(state, coherence, conflict, identity_bias)

        winner = max(scores, key=scores.get)

        mapping = {
            "stabilizer": "stay",
            "explorer": "right",
            "amplifier": "left"
        }

        return mapping[winner], scores


# ---------------------------
# 🧬 IDENTITY / VALUES
# ---------------------------

class Identity:
    def __init__(self):
        self.preferences = defaultdict(float)

    def update(self, action, reward):
        self.preferences[action] += reward * 0.1

    def bias(self):
        return self.preferences


# ---------------------------
# 🔧 SAFE META-ADAPTATION
# ---------------------------

class MetaLearner:
    def __init__(self):
        self.lr = 0.1

    def update_voice_bias(self, dialogue, reward):
        for v in dialogue.voices:
            v.bias += self.lr * (reward - 0.5)  # center around neutral


# ---------------------------
# 🧠 ENGINE v6
# ---------------------------

class CoherenceEngineV6:
    def __init__(self):
        self.env = Environment1D(attractor=0.0)

        self.position = random.uniform(-2, 2)
        self.state = np.array([self.position])

        self.memory = Memory()
        self.dialogue = Dialogue()
        self.identity = Identity()
        self.meta = MetaLearner()

        self.narrative = deque(maxlen=10)

    # -----------------------
    def coherence(self):
        states = self.memory.recent_states()
        if len(states) < 2:
            return 0
        return 1 / (1 + np.var(states))

    def conflict(self):
        states = self.memory.recent_states()
        if len(states) < 2:
            return 0
        return np.linalg.norm(states[-1] - np.mean(states))

    # -----------------------
    def step(self):
        coherence = self.coherence()
        conflict = self.conflict()

        action, scores = self.dialogue.decide(
            self.state,
            coherence,
            conflict,
            self.identity.bias()
        )

        # interact with world
        self.position, reward = self.env.step(self.position, action)
        self.state = np.array([self.position])

        # store experience
        exp = {
            "state": self.state,
            "action": action,
            "reward": reward
        }
        self.memory.add(exp)

        # update identity
        self.identity.update(action, reward)

        # meta learning (safe)
        self.meta.update_voice_bias(self.dialogue, reward)

        # narrative
        sentence = f"I chose {action} → reward {round(reward,2)}"
        self.narrative.append(sentence)

        return {
            "position": self.position,
            "action": action,
            "reward": reward,
            "coherence": coherence,
            "conflict": conflict,
            "identity": dict(self.identity.preferences),
            "dialogue_scores": scores,
            "narrative": " | ".join(self.narrative)
        }


# ---------------------------
# 🔹 TEST
# ---------------------------

if __name__ == "__main__":
    engine = CoherenceEngineV6()

    for i in range(30):
        result = engine.step()

        print(f"\nStep {i}")
        print("Position:", round(result["position"], 2))
        print("Action:", result["action"])
        print("Reward:", result["reward"])
        print("Coherence:", result["coherence"])
        print("Identity:", result["identity"])
        print("Narrative:", result["narrative"])
