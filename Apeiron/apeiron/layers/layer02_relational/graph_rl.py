"""
graph_rl.py – Reinforcement Learning on Graphs / Hypergraphs
=============================================================
Provides:
  - GraphEnv        : navigate a graph to reach a target node
  - ResourceCollectionEnv : collect resources on nodes
  - GraphCoveringEnv : visit all nodes
  - DeliveryEnv      : pick up and deliver a package
  - HypergraphEnv    : RL environment on a hypergraph (1-skeleton)
  - QLearningAgent   : tabular Q-learning agent
  - DQNAgent         : deep Q-network agent (requires PyTorch)
  - RLAgent          : simple Q-learning agent for HypergraphEnv

All environments and agents degrade gracefully if gym is not installed.
"""

from __future__ import annotations

import logging
import random
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – graceful degradation
# ---------------------------------------------------------------------------

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYM = True
except ImportError:
    try:
        import gym
        from gym import spaces
        HAS_GYM = True
    except ImportError:
        HAS_GYM = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ---------------------------------------------------------------------------
# GYM‑based environments
# ---------------------------------------------------------------------------
if HAS_GYM and HAS_NETWORKX:

    class GraphEnv(gym.Env):
        """
        Navigate on a NetworkX graph to reach a target node.

        Actions: move to a neighbour by index (0..max_degree-1).
        Observation: current node index (Discrete).
        Reward: +1 for reaching target, -0.01 per step.
        Episode ends when target is reached or max_steps exceeded.
        """
        metadata = {'render.modes': ['human']}

        def __init__(
            self,
            graph: nx.Graph,
            target_node: Any,
            max_steps: int = 50,
            allow_stay: bool = False,
            reward_target: float = 1.0,
            step_penalty: float = -0.01,
        ):
            super().__init__()
            self.graph = graph
            self.nodes = list(graph.nodes())
            self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
            self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
            self.n_nodes = len(self.nodes)
            self.target_node = target_node
            self.target_idx = self.node_to_idx[target_node]
            self.max_steps = max_steps
            self.allow_stay = allow_stay
            self.reward_target = reward_target
            self.step_penalty = step_penalty

            max_deg = max(dict(graph.degree()).values())
            self.action_space = spaces.Discrete(max_deg + (1 if allow_stay else 0))
            self.observation_space = spaces.Discrete(self.n_nodes)
            self.current_idx = None
            self.steps = 0

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            candidates = [i for i in range(self.n_nodes) if i != self.target_idx]
            self.current_idx = np.random.choice(candidates)
            self.steps = 0
            return self.current_idx, {}

        def step(self, action):
            self.steps += 1
            neighbours = list(self.graph.neighbors(self.idx_to_node[self.current_idx]))
            neigh_idx = [self.node_to_idx[n] for n in neighbours]
            if action < len(neigh_idx):
                next_idx = neigh_idx[action]
            elif self.allow_stay and action == len(neigh_idx):
                next_idx = self.current_idx
            else:
                next_idx = self.current_idx
            self.current_idx = next_idx
            terminated = self.current_idx == self.target_idx
            truncated = self.steps >= self.max_steps
            reward = self.reward_target if terminated else self.step_penalty
            return self.current_idx, reward, terminated, truncated, {}

        def render(self):
            print(f"Step {self.steps}, node {self.idx_to_node[self.current_idx]}")


    class ResourceCollectionEnv(gym.Env):
        """
        Collect resources from nodes. Agent gets reward equal to resource
        value when visiting a node; the resource is then consumed.
        Observation: one‑hot current node + remaining resource levels.
        """
        metadata = {'render.modes': ['human']}

        def __init__(self, graph: nx.Graph, max_steps: int = 50,
                     resource_values: Optional[Dict[Any, float]] = None):
            super().__init__()
            self.graph = graph
            self.nodes = list(graph.nodes())
            self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
            self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
            self.n_nodes = len(self.nodes)

            if resource_values is None:
                resource_values = {n: 1.0 for n in self.nodes}
            self.initial_resources = np.array([resource_values.get(n, 0.0) for n in self.nodes])
            self.resources = self.initial_resources.copy()

            self.max_steps = max_steps
            self.current_idx = None
            self.steps = 0

            max_deg = max(dict(graph.degree()).values())
            self.action_space = spaces.Discrete(max_deg)
            self.observation_space = spaces.Box(
                low=0.0, high=1.0,
                shape=(self.n_nodes + self.n_nodes,), dtype=np.float32,
            )

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self.current_idx = np.random.randint(self.n_nodes)
            self.resources = self.initial_resources.copy()
            self.steps = 0
            return self._get_obs(), {}

        def step(self, action):
            self.steps += 1
            cur = self.idx_to_node[self.current_idx]
            neighbours = list(self.graph.neighbors(cur))
            if action < len(neighbours):
                self.current_idx = self.node_to_idx[neighbours[action]]
            reward = self.resources[self.current_idx]
            self.resources[self.current_idx] = 0.0
            terminated = self.resources.sum() == 0
            truncated = self.steps >= self.max_steps
            return self._get_obs(), reward, terminated, truncated, {}

        def _get_obs(self):
            oh = np.zeros(self.n_nodes, dtype=np.float32)
            oh[self.current_idx] = 1.0
            res = self.resources / (self.initial_resources + 1e-8)
            return np.concatenate([oh, res])

        def render(self):
            coll = self.initial_resources.sum() - self.resources.sum()
            print(f"Step {self.steps}, node {self.idx_to_node[self.current_idx]}, collected {coll}")


    class GraphCoveringEnv(gym.Env):
        """
        Cover all nodes of a graph. Reward: +1 for a new node, -0.01 per step.
        Episode ends when all nodes are visited or max_steps exceeded.
        """
        metadata = {'render.modes': ['human']}

        def __init__(self, graph: nx.Graph, max_steps: int = 100):
            super().__init__()
            self.graph = graph
            self.nodes = list(graph.nodes())
            self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
            self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
            self.n_nodes = len(self.nodes)

            self.max_steps = max_steps
            self.current_idx = None
            self.visited = None
            self.steps = 0

            max_deg = max(dict(graph.degree()).values())
            self.action_space = spaces.Discrete(max_deg)
            self.observation_space = spaces.Box(
                low=0.0, high=1.0,
                shape=(self.n_nodes + self.n_nodes,), dtype=np.float32,
            )

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self.current_idx = np.random.randint(self.n_nodes)
            self.visited = np.zeros(self.n_nodes, dtype=bool)
            self.visited[self.current_idx] = True
            self.steps = 0
            return self._get_obs(), {}

        def step(self, action):
            self.steps += 1
            cur = self.idx_to_node[self.current_idx]
            neighbours = list(self.graph.neighbors(cur))
            if action < len(neighbours):
                self.current_idx = self.node_to_idx[neighbours[action]]
            reward_new = 0.0
            if not self.visited[self.current_idx]:
                reward_new = 1.0
                self.visited[self.current_idx] = True
            reward = reward_new - 0.01
            terminated = self.visited.all()
            truncated = self.steps >= self.max_steps
            return self._get_obs(), reward, terminated, truncated, {}

        def _get_obs(self):
            oh = np.zeros(self.n_nodes, dtype=np.float32)
            oh[self.current_idx] = 1.0
            return np.concatenate([oh, self.visited.astype(np.float32)])

        def render(self):
            print(f"Step {self.steps}, node {self.idx_to_node[self.current_idx]}, "
                  f"visited {self.visited.sum()}/{self.n_nodes}")


    class DeliveryEnv(gym.Env):
        """
        Pick up a package at pickup_node and deliver to delivery_node.
        Reward: +10 on delivery, -0.1 per step.
        """
        metadata = {'render.modes': ['human']}

        def __init__(self, graph: nx.Graph, pickup_node: Any, delivery_node: Any,
                     max_steps: int = 100):
            super().__init__()
            self.graph = graph
            self.nodes = list(graph.nodes())
            self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
            self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
            self.n_nodes = len(self.nodes)

            self.pickup_idx = self.node_to_idx[pickup_node]
            self.delivery_idx = self.node_to_idx[delivery_node]
            self.max_steps = max_steps
            self.current_idx = None
            self.package_picked = False
            self.steps = 0

            max_deg = max(dict(graph.degree()).values())
            self.action_space = spaces.Discrete(max_deg)
            self.observation_space = spaces.Box(
                low=0.0, high=1.0,
                shape=(self.n_nodes + 1,), dtype=np.float32,
            )

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self.current_idx = self.pickup_idx
            self.package_picked = False
            self.steps = 0
            return self._get_obs(), {}

        def step(self, action):
            self.steps += 1
            cur = self.idx_to_node[self.current_idx]
            neighbours = list(self.graph.neighbors(cur))
            if action < len(neighbours):
                self.current_idx = self.node_to_idx[neighbours[action]]
            if self.current_idx == self.pickup_idx and not self.package_picked:
                self.package_picked = True
            delivered = self.current_idx == self.delivery_idx and self.package_picked
            reward = 10.0 if delivered else -0.1
            terminated = delivered
            truncated = self.steps >= self.max_steps
            return self._get_obs(), reward, terminated, truncated, {}

        def _get_obs(self):
            oh = np.zeros(self.n_nodes, dtype=np.float32)
            oh[self.current_idx] = 1.0
            flag = np.array([1.0 if self.package_picked else 0.0], dtype=np.float32)
            return np.concatenate([oh, flag])

        def render(self):
            status = "picked" if self.package_picked else "not picked"
            print(f"Step {self.steps}, node {self.idx_to_node[self.current_idx]}, {status}")

else:
    # Dummy classes so the module loads even without gym
    class GraphEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("gym is required for GraphEnv")

    class ResourceCollectionEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("gym is required for ResourceCollectionEnv")

    class GraphCoveringEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("gym is required for GraphCoveringEnv")

    class DeliveryEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("gym is required for DeliveryEnv")


# ---------------------------------------------------------------------------
# Hypergraph‑specific RL (from hypergraph_relations.py)
# ---------------------------------------------------------------------------
if HAS_GYM and HAS_NETWORKX:

    class HypergraphEnv(gym.Env):
        """
        RL environment on the 1‑skeleton of a hypergraph.
        (Imported from hypergraph_relations.py)
        """
        def __init__(self, hypergraph, target: Any, max_steps: int = 100):
            super().__init__()
            self.hypergraph = hypergraph
            self.target = target
            self.max_steps = max_steps
            self.vertices = list(hypergraph.vertices)
            self.adj = self._build_adjacency()
            self.action_space = spaces.Discrete(len(self.vertices))
            self.observation_space = spaces.Discrete(len(self.vertices))
            self.current_vertex = None
            self.steps = 0

        def _build_adjacency(self):
            G = nx.Graph()
            G.add_nodes_from(self.vertices)
            for edge in self.hypergraph.simplicial_complex.get(1, []):
                v1, v2 = list(edge)[:2]
                G.add_edge(v1, v2)
            return {v: list(G.neighbors(v)) for v in self.vertices}

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self.current_vertex = np.random.choice(self.vertices)
            self.steps = 0
            return self.vertices.index(self.current_vertex), {}

        def step(self, action):
            self.steps += 1
            next_vertex = self.vertices[action]
            if next_vertex in self.adj[self.current_vertex]:
                self.current_vertex = next_vertex
            reward = 1.0 if self.current_vertex == self.target else -0.01
            terminated = self.current_vertex == self.target
            truncated = self.steps >= self.max_steps
            return self.vertices.index(self.current_vertex), reward, terminated, truncated, {}

        def render(self):
            print(f"Step {self.steps}, vertex {self.current_vertex}")

else:
    class HypergraphEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError("gym and networkx are required for HypergraphEnv")


# ---------------------------------------------------------------------------
# Q‑learning agents
# ---------------------------------------------------------------------------

class QLearningAgent:
    """
    Tabular Q‑learning agent for discrete observation and action spaces.

    Parameters
    ----------
    n_states, n_actions : sizes of state and action spaces.
    learning_rate, discount_factor : standard RL parameters.
    epsilon, epsilon_decay, epsilon_min : exploration schedule.
    """
    def __init__(
        self,
        n_states: int,
        n_actions: int,
        learning_rate: float = 0.1,
        discount_factor: float = 0.99,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = np.zeros((n_states, n_actions))

    def act(self, state: int, explore: bool = True) -> int:
        if explore and np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(self.q_table[state]))

    def update(self, state: int, action: int, reward: float, next_state: int, done: bool):
        best_next = 0.0 if done else np.max(self.q_table[next_state])
        target = reward + self.gamma * best_next
        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])
        if done:
            self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

    def save(self, path: str):
        np.save(path, self.q_table)

    def load(self, path: str):
        self.q_table = np.load(path)


# Simple RLAgent for HypergraphEnv (from hypergraph_relations.py)
class RLAgent:
    """Q‑learning agent specifically for HypergraphEnv."""
    def __init__(self, env: HypergraphEnv, learning_rate: float = 0.1, discount: float = 0.95):
        self.env = env
        self.lr = learning_rate
        self.gamma = discount
        self.q_table = np.zeros((len(env.vertices), env.action_space.n))

    def train(self, episodes: int = 1000):
        for _ in range(episodes):
            state, _ = self.env.reset()
            done = False
            while not done:
                if np.random.random() < 0.1:
                    action = self.env.action_space.sample()
                else:
                    action = np.argmax(self.q_table[state])
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                done = terminated or truncated
                best_next = np.max(self.q_table[next_state])
                self.q_table[state, action] += self.lr * (reward + self.gamma * best_next - self.q_table[state, action])
                state = next_state

    def act(self, state: int, explore: bool = False) -> int:
        if explore and np.random.random() < 0.1:
            return self.env.action_space.sample()
        return int(np.argmax(self.q_table[state]))


# ---------------------------------------------------------------------------
# Deep Q‑Network agent (optional)
# ---------------------------------------------------------------------------
if HAS_TORCH:

    class DQN(nn.Module):
        """Simple feed‑forward network for DQN."""
        def __init__(self, input_dim, hidden_dim, output_dim):
            super().__init__()
            self.fc = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, output_dim),
            )

        def forward(self, x):
            return self.fc(x)

    class DQNAgent:
        """
        Deep Q‑Network agent with experience replay and target network.
        """
        def __init__(
            self,
            state_dim: int,
            action_dim: int,
            hidden_dim: int = 64,
            learning_rate: float = 1e-3,
            discount_factor: float = 0.99,
            epsilon: float = 1.0,
            epsilon_decay: float = 0.995,
            epsilon_min: float = 0.01,
            buffer_size: int = 10000,
            batch_size: int = 32,
            target_update_freq: int = 100,
            device: str = 'cpu',
        ):
            self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
            self.action_dim = action_dim
            self.gamma = discount_factor
            self.epsilon = epsilon
            self.epsilon_decay = epsilon_decay
            self.epsilon_min = epsilon_min
            self.batch_size = batch_size
            self.target_update_freq = target_update_freq
            self.step_counter = 0

            self.q_net = DQN(state_dim, hidden_dim, action_dim).to(self.device)
            self.target_net = DQN(state_dim, hidden_dim, action_dim).to(self.device)
            self.target_net.load_state_dict(self.q_net.state_dict())
            self.optimizer = optim.Adam(self.q_net.parameters(), lr=learning_rate)
            self.loss_fn = nn.MSELoss()
            self.replay_buffer = deque(maxlen=buffer_size)

        def act(self, state: np.ndarray, explore: bool = True) -> int:
            if explore and np.random.random() < self.epsilon:
                return np.random.randint(self.action_dim)
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                return int(self.q_net(state_t).argmax().item())

        def store_transition(self, state, action, reward, next_state, done):
            self.replay_buffer.append((state, action, reward, next_state, done))

        def train_step(self) -> Optional[float]:
            if len(self.replay_buffer) < self.batch_size:
                return None
            batch = random.sample(self.replay_buffer, self.batch_size)
            states = torch.FloatTensor(np.array([t[0] for t in batch])).to(self.device)
            actions = torch.LongTensor([t[1] for t in batch]).to(self.device)
            rewards = torch.FloatTensor([t[2] for t in batch]).to(self.device)
            next_states = torch.FloatTensor(np.array([t[3] for t in batch])).to(self.device)
            dones = torch.BoolTensor([t[4] for t in batch]).to(self.device)

            q_values = self.q_net(states).gather(1, actions.unsqueeze(1)).squeeze()
            with torch.no_grad():
                next_q = self.target_net(next_states).max(1)[0]
                next_q[dones] = 0.0
                target = rewards + self.gamma * next_q

            loss = self.loss_fn(q_values, target)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)
            self.step_counter += 1
            if self.step_counter % self.target_update_freq == 0:
                self.target_net.load_state_dict(self.q_net.state_dict())
            return loss.item()

        def save(self, path: str):
            torch.save({
                'q_net': self.q_net.state_dict(),
                'target_net': self.target_net.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
            }, path)

        def load(self, path: str):
            ckpt = torch.load(path, map_location=self.device)
            self.q_net.load_state_dict(ckpt['q_net'])
            self.target_net.load_state_dict(ckpt['target_net'])
            self.optimizer.load_state_dict(ckpt['optimizer'])
            self.epsilon = ckpt['epsilon']

else:
    DQNAgent = None
    DQN = None


# ---------------------------------------------------------------------------
# Training loops
# ---------------------------------------------------------------------------

def train_agent(env, agent, episodes: int = 1000, max_steps: Optional[int] = None,
                verbose: bool = False) -> Dict[str, List[float]]:
    """Generic training loop for QLearningAgent or similar."""
    rewards = []
    steps_list = []
    for ep in range(episodes):
        state, _ = env.reset()
        done = False
        total_reward = 0
        step = 0
        while not done:
            action = agent.act(state, explore=True)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            agent.update(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            step += 1
            if max_steps and step >= max_steps:
                break
        rewards.append(total_reward)
        steps_list.append(step)
        if verbose and (ep+1) % 10 == 0:
            avg_r = np.mean(rewards[-10:])
            print(f"Episode {ep+1}, avg reward {avg_r:.2f}, steps {step}")
    return {'episode_rewards': rewards, 'episode_steps': steps_list}


def train_dqn(env, agent: DQNAgent, episodes: int = 1000,
              max_steps: Optional[int] = None, verbose: bool = False) -> Dict[str, List[float]]:
    """Training loop for DQN agent."""
    rewards = []
    steps_list = []
    for ep in range(episodes):
        state, _ = env.reset()
        done = False
        total_reward = 0
        step = 0
        while not done:
            action = agent.act(state, explore=True)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            agent.store_transition(state, action, reward, next_state, done)
            agent.train_step()
            state = next_state
            total_reward += reward
            step += 1
            if max_steps and step >= max_steps:
                break
        rewards.append(total_reward)
        steps_list.append(step)
        if verbose and (ep+1) % 10 == 0:
            avg_r = np.mean(rewards[-10:])
            print(f"Episode {ep+1}, avg reward {avg_r:.2f}, steps {step}")
    return {'episode_rewards': rewards, 'episode_steps': steps_list}