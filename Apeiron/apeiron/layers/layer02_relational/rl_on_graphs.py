"""
REINFORCEMENT LEARNING ON GRAPHS – ULTIMATE IMPLEMENTATION
============================================================
This module provides reinforcement learning environments and agents
for graph‑based tasks. It includes:

- `GraphEnv`: a simple navigation environment on a NetworkX graph.
- `ResourceCollectionEnv`: an environment where an agent collects resources on nodes.
- `GraphCoveringEnv`: an environment for graph covering problems.
- `DeliveryEnv`: an environment for package delivery on a graph.
- `QLearningAgent`: tabular Q‑learning agent.
- `DQNAgent`: Deep Q‑Network agent (requires PyTorch).
- Training loops and evaluation utilities.

All features degrade gracefully if required libraries are missing.
"""

import logging
import numpy as np
from typing import Optional, Dict, List, Any, Tuple, Union, Callable
from collections import defaultdict, deque
import random

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# NetworkX for graph operations
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# Gymnasium (or Gym) for RL environments
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

# PyTorch for DQN
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logger = logging.getLogger(__name__)


# ============================================================================
# ENVIRONMENTS
# ============================================================================

class GraphEnv:
    """
    A simple navigation environment on a graph.
    The agent starts at a random node and must reach a target node.
    Actions: move to a neighbour (by index) or stay (if allowed).
    Observation: current node index.
    Reward: +1 for reaching target, -0.01 per step (encourages efficiency).
    Episode ends when target is reached or max_steps exceeded.
    """
    def __init__(self, graph: 'nx.Graph', target_node: Any,
                 max_steps: int = 50, allow_stay: bool = False,
                 reward_target: float = 1.0, step_penalty: float = -0.01):
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required for GraphEnv")
        self.graph = graph
        self.nodes = list(graph.nodes())
        self.node_to_idx = {node: i for i, node in enumerate(self.nodes)}
        self.idx_to_node = {i: node for i, node in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)
        self.target_node = target_node
        self.target_idx = self.node_to_idx[target_node]
        self.max_steps = max_steps
        self.allow_stay = allow_stay
        self.reward_target = reward_target
        self.step_penalty = step_penalty

        # Action space: for each node, the agent can choose a neighbour (or stay)
        # We'll use a discrete action space where each action corresponds to moving to a specific neighbour.
        # But neighbours differ per node, so we need a dynamic action masking.
        # For simplicity, we define action space as the maximum number of neighbours + 1 (stay).
        self.max_degree = max(dict(graph.degree()).values())
        self.action_space = spaces.Discrete(self.max_degree + (1 if allow_stay else 0))

        # Observation space: current node index
        self.observation_space = spaces.Discrete(self.n_nodes)

        self.current_idx = None
        self.steps = 0

    def reset(self, seed: Optional[int] = None) -> Tuple[int, Dict]:
        """Reset environment, return initial observation."""
        if seed is not None:
            np.random.seed(seed)
        # Start at a random node (not the target)
        candidates = [i for i in range(self.n_nodes) if i != self.target_idx]
        self.current_idx = np.random.choice(candidates)
        self.steps = 0
        return self.current_idx, {}

    def step(self, action: int) -> Tuple[int, float, bool, bool, Dict]:
        """
        Take an action.
        Returns: next_obs, reward, terminated, truncated, info.
        """
        self.steps += 1
        # Decode action: move to neighbour if action < degree, else stay if allowed
        neighbours = list(self.graph.neighbors(self.idx_to_node[self.current_idx]))
        neighbour_indices = [self.node_to_idx[n] for n in neighbours]

        if action < len(neighbour_indices):
            next_idx = neighbour_indices[action]
        elif self.allow_stay and action == len(neighbour_indices):
            next_idx = self.current_idx  # stay
        else:
            # Invalid action: stay in place (or we could penalize)
            next_idx = self.current_idx

        self.current_idx = next_idx

        # Check termination
        terminated = (self.current_idx == self.target_idx)
        truncated = (self.steps >= self.max_steps)
        reward = self.reward_target if terminated else self.step_penalty

        return self.current_idx, reward, terminated, truncated, {}

    def render(self):
        """Print current state."""
        print(f"Step {self.steps}, current node: {self.idx_to_node[self.current_idx]}")


class ResourceCollectionEnv(gym.Env if HAS_GYM else object):
    """
    Environment where an agent moves on a graph and collects resources from nodes.
    Each node has a resource value (initially positive). The agent gets reward equal to the resource
    when visiting a node, and the resource is consumed (set to 0). Episode ends after max_steps
    or when all resources are collected.
    Observation: vector of current node (one‑hot) and remaining resources (n_nodes).
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, graph: 'nx.Graph', max_steps: int = 50,
                 resource_values: Optional[Dict[Any, float]] = None):
        if not HAS_NETWORKX or not HAS_GYM:
            raise ImportError("NetworkX and gym are required for ResourceCollectionEnv")
        self.graph = graph
        self.nodes = list(graph.nodes())
        self.node_to_idx = {node: i for i, node in enumerate(self.nodes)}
        self.idx_to_node = {i: node for i, node in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)

        if resource_values is None:
            resource_values = {node: 1.0 for node in self.nodes}
        self.initial_resources = np.array([resource_values.get(node, 0.0) for node in self.nodes])
        self.resources = self.initial_resources.copy()

        self.max_steps = max_steps
        self.current_idx = 0
        self.steps = 0

        # Action: move to neighbour (index of neighbour within list)
        self.max_degree = max(dict(graph.degree()).values())
        self.action_space = spaces.Discrete(self.max_degree)

        # Observation: current node (one‑hot) + resource levels
        self.observation_space = spaces.Box(low=0.0, high=1.0,
                                            shape=(self.n_nodes + self.n_nodes,),
                                            dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # Start at a random node
        self.current_idx = np.random.randint(self.n_nodes)
        self.resources = self.initial_resources.copy()
        self.steps = 0
        return self._get_obs(), {}

    def step(self, action):
        self.steps += 1
        # Determine neighbour
        current_node = self.idx_to_node[self.current_idx]
        neighbours = list(self.graph.neighbors(current_node))
        if action < len(neighbours):
            next_node = neighbours[action]
            self.current_idx = self.node_to_idx[next_node]
        else:
            # Invalid action: stay
            pass

        # Collect resource
        reward = self.resources[self.current_idx]
        self.resources[self.current_idx] = 0.0

        # Check termination
        terminated = (self.resources.sum() == 0)  # all collected
        truncated = self.steps >= self.max_steps

        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        # One‑hot for current node
        node_one_hot = np.zeros(self.n_nodes, dtype=np.float32)
        node_one_hot[self.current_idx] = 1.0
        # Resource levels (normalised?)
        res = self.resources / (self.initial_resources + 1e-8)
        return np.concatenate([node_one_hot, res])

    def render(self, mode='human'):
        print(f"Step {self.steps}, current node: {self.idx_to_node[self.current_idx]}, "
              f"resources collected: {self.initial_resources.sum() - self.resources.sum()}")


class GraphCoveringEnv(gym.Env if HAS_GYM else object):
    """
    Environment for graph covering problem: agent must visit all nodes.
    Reward: +1 for visiting a new node, -0.01 per step.
    Episode ends when all nodes visited or max_steps exceeded.
    Observation: current node (one‑hot) and visited mask.
    """
    def __init__(self, graph: 'nx.Graph', max_steps: int = 100):
        if not HAS_NETWORKX or not HAS_GYM:
            raise ImportError("NetworkX and gym are required for GraphCoveringEnv")
        self.graph = graph
        self.nodes = list(graph.nodes())
        self.node_to_idx = {node: i for i, node in enumerate(self.nodes)}
        self.idx_to_node = {i: node for i, node in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)

        self.max_steps = max_steps
        self.current_idx = 0
        self.visited = None
        self.steps = 0

        self.max_degree = max(dict(graph.degree()).values())
        self.action_space = spaces.Discrete(self.max_degree)
        self.observation_space = spaces.Box(low=0.0, high=1.0,
                                            shape=(self.n_nodes + self.n_nodes,),
                                            dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.current_idx = np.random.randint(self.n_nodes)
        self.visited = np.zeros(self.n_nodes, dtype=bool)
        self.visited[self.current_idx] = True
        self.steps = 0
        return self._get_obs(), {}

    def step(self, action):
        self.steps += 1
        current_node = self.idx_to_node[self.current_idx]
        neighbours = list(self.graph.neighbors(current_node))
        if action < len(neighbours):
            next_node = neighbours[action]
            self.current_idx = self.node_to_idx[next_node]
        # else: stay

        new_node_reward = 0.0
        if not self.visited[self.current_idx]:
            new_node_reward = 1.0
            self.visited[self.current_idx] = True

        reward = new_node_reward - 0.01
        terminated = self.visited.all()
        truncated = self.steps >= self.max_steps

        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        node_one_hot = np.zeros(self.n_nodes, dtype=np.float32)
        node_one_hot[self.current_idx] = 1.0
        visited_float = self.visited.astype(np.float32)
        return np.concatenate([node_one_hot, visited_float])

    def render(self, mode='human'):
        print(f"Step {self.steps}, current node: {self.idx_to_node[self.current_idx]}, "
              f"visited {self.visited.sum()}/{self.n_nodes}")


class DeliveryEnv(gym.Env if HAS_GYM else object):
    """
    Environment for package delivery: agent starts at pickup node, must go to delivery node.
    Reward: +10 on delivery, -0.1 per step.
    Observation: current node (one‑hot) and a flag whether package is picked up (0/1).
    """
    def __init__(self, graph: 'nx.Graph', pickup_node: Any, delivery_node: Any,
                 max_steps: int = 100):
        if not HAS_NETWORKX or not HAS_GYM:
            raise ImportError("NetworkX and gym are required for DeliveryEnv")
        self.graph = graph
        self.nodes = list(graph.nodes())
        self.node_to_idx = {node: i for i, node in enumerate(self.nodes)}
        self.idx_to_node = {i: node for i, node in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)

        self.pickup_idx = self.node_to_idx[pickup_node]
        self.delivery_idx = self.node_to_idx[delivery_node]
        self.max_steps = max_steps
        self.current_idx = None
        self.package_picked = False
        self.steps = 0

        self.max_degree = max(dict(graph.degree()).values())
        self.action_space = spaces.Discrete(self.max_degree)
        self.observation_space = spaces.Box(low=0.0, high=1.0,
                                            shape=(self.n_nodes + 1,), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # Start at pickup node
        self.current_idx = self.pickup_idx
        self.package_picked = False
        self.steps = 0
        return self._get_obs(), {}

    def step(self, action):
        self.steps += 1
        current_node = self.idx_to_node[self.current_idx]
        neighbours = list(self.graph.neighbors(current_node))
        if action < len(neighbours):
            next_node = neighbours[action]
            self.current_idx = self.node_to_idx[next_node]

        # Pick up if at pickup and not yet picked
        if self.current_idx == self.pickup_idx and not self.package_picked:
            self.package_picked = True

        # Delivery if at delivery and package picked
        delivered = (self.current_idx == self.delivery_idx and self.package_picked)

        reward = 10.0 if delivered else -0.1
        terminated = delivered
        truncated = self.steps >= self.max_steps

        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        node_one_hot = np.zeros(self.n_nodes, dtype=np.float32)
        node_one_hot[self.current_idx] = 1.0
        flag = np.array([1.0 if self.package_picked else 0.0], dtype=np.float32)
        return np.concatenate([node_one_hot, flag])

    def render(self, mode='human'):
        status = "picked" if self.package_picked else "not picked"
        print(f"Step {self.steps}, node: {self.idx_to_node[self.current_idx]}, package {status}")


# ============================================================================
# AGENTS
# ============================================================================

class QLearningAgent:
    """
    Tabular Q‑learning agent for discrete state and action spaces.
    Uses epsilon‑greedy exploration.
    """
    def __init__(self, n_states: int, n_actions: int,
                 learning_rate: float = 0.1,
                 discount_factor: float = 0.99,
                 epsilon: float = 0.1,
                 epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        self.q_table = np.zeros((n_states, n_actions))

    def act(self, state: int, explore: bool = True) -> int:
        """Choose action using epsilon‑greedy."""
        if explore and np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(self.q_table[state]))

    def update(self, state: int, action: int, reward: float,
               next_state: int, done: bool):
        """Q‑learning update."""
        best_next = np.max(self.q_table[next_state]) if not done else 0.0
        target = reward + self.gamma * best_next
        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])

        if done:
            self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

    def save(self, path: str):
        np.save(path, self.q_table)

    def load(self, path: str):
        self.q_table = np.load(path)


if HAS_TORCH:
    class DQN(nn.Module):
        """Simple neural network for DQN."""
        def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
            super().__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim)
            self.fc3 = nn.Linear(hidden_dim, output_dim)

        def forward(self, x):
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            return self.fc3(x)


    class DQNAgent:
        """
        Deep Q‑Network agent with experience replay and target network.
        """
        def __init__(self,
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
                     device: str = 'cpu'):
            self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
            self.action_dim = action_dim
            self.gamma = discount_factor
            self.epsilon = epsilon
            self.epsilon_decay = epsilon_decay
            self.epsilon_min = epsilon_min
            self.batch_size = batch_size
            self.target_update_freq = target_update_freq
            self.step_counter = 0

            self.q_network = DQN(state_dim, hidden_dim, action_dim).to(self.device)
            self.target_network = DQN(state_dim, hidden_dim, action_dim).to(self.device)
            self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
            self.loss_fn = nn.MSELoss()

            self.replay_buffer = deque(maxlen=buffer_size)

            self._update_target()

        def _update_target(self):
            self.target_network.load_state_dict(self.q_network.state_dict())

        def act(self, state: np.ndarray, explore: bool = True) -> int:
            """Epsilon‑greedy action selection."""
            if explore and np.random.random() < self.epsilon:
                return np.random.randint(self.action_dim)
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_vals = self.q_network(state_t)
            return int(q_vals.argmax().item())

        def store_transition(self, state, action, reward, next_state, done):
            self.replay_buffer.append((state, action, reward, next_state, done))

        def train_step(self) -> Optional[float]:
            """Perform one training step using a batch from replay buffer."""
            if len(self.replay_buffer) < self.batch_size:
                return None

            batch = random.sample(self.replay_buffer, self.batch_size)
            states = torch.FloatTensor(np.array([t[0] for t in batch])).to(self.device)
            actions = torch.LongTensor([t[1] for t in batch]).to(self.device)
            rewards = torch.FloatTensor([t[2] for t in batch]).to(self.device)
            next_states = torch.FloatTensor(np.array([t[3] for t in batch])).to(self.device)
            dones = torch.BoolTensor([t[4] for t in batch]).to(self.device)

            # Current Q values
            q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze()

            # Target Q values
            with torch.no_grad():
                next_q = self.target_network(next_states).max(1)[0]
                next_q[dones] = 0.0
                target_q = rewards + self.gamma * next_q

            loss = self.loss_fn(q_values, target_q)

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # Update epsilon
            self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

            # Update target network periodically
            self.step_counter += 1
            if self.step_counter % self.target_update_freq == 0:
                self._update_target()

            return loss.item()

        def save(self, path: str):
            torch.save({
                'q_network': self.q_network.state_dict(),
                'target_network': self.target_network.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'epsilon': self.epsilon
            }, path)

        def load(self, path: str):
            checkpoint = torch.load(path, map_location=self.device)
            self.q_network.load_state_dict(checkpoint['q_network'])
            self.target_network.load_state_dict(checkpoint['target_network'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.epsilon = checkpoint['epsilon']

else:
    class DQNAgent:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is required for DQNAgent")


# ============================================================================
# TRAINING LOOP
# ============================================================================

def train_agent(env, agent, episodes: int = 1000,
                max_steps_per_episode: Optional[int] = None,
                verbose: bool = False,
                render_every: Optional[int] = None) -> Dict[str, List[float]]:
    """
    Generic training loop for an agent interacting with an environment.

    Args:
        env: environment (must have reset() and step()).
        agent: agent with act() and update() methods.
        episodes: number of episodes.
        max_steps_per_episode: optional limit.
        verbose: if True, print episode stats.
        render_every: if provided, render every N episodes.

    Returns:
        Dict with lists of episode rewards and steps.
    """
    episode_rewards = []
    episode_steps = []
    for ep in range(episodes):
        state, _ = env.reset()
        done = False
        total_reward = 0
        steps = 0
        while not done:
            action = agent.act(state, explore=True)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            agent.update(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            steps += 1
            if max_steps_per_episode and steps >= max_steps_per_episode:
                break
        episode_rewards.append(total_reward)
        episode_steps.append(steps)

        if verbose and (ep+1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_steps = np.mean(episode_steps[-10:])
            print(f"Episode {ep+1}, avg reward: {avg_reward:.2f}, avg steps: {avg_steps:.1f}")

        if render_every and (ep+1) % render_every == 0:
            env.render()

    return {'episode_rewards': episode_rewards, 'episode_steps': episode_steps}


def train_dqn(env, agent: DQNAgent, episodes: int = 1000,
              max_steps_per_episode: Optional[int] = None,
              verbose: bool = False) -> Dict[str, List[float]]:
    """
    Specialised training loop for DQN agent (uses train_step after each episode).
    """
    episode_rewards = []
    episode_steps = []
    for ep in range(episodes):
        state, _ = env.reset()
        done = False
        total_reward = 0
        steps = 0
        while not done:
            action = agent.act(state, explore=True)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            agent.store_transition(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            steps += 1
            if max_steps_per_episode and steps >= max_steps_per_episode:
                break
            # Train at each step (or accumulate and train after episode)
            agent.train_step()
        episode_rewards.append(total_reward)
        episode_steps.append(steps)

        if verbose and (ep+1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_steps = np.mean(episode_steps[-10:])
            print(f"Episode {ep+1}, avg reward: {avg_reward:.2f}, avg steps: {avg_steps:.1f}")

    return {'episode_rewards': episode_rewards, 'episode_steps': episode_steps}


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Run a simple demo on a small graph."""
    if not HAS_NETWORKX:
        print("NetworkX required for demo.")
        return

    # Create a small graph (a path)
    G = nx.path_graph(5)

    print("="*60)
    print("RL ON GRAPHS DEMO")
    print("="*60)

    # --- QLearningAgent on GraphEnv ---
    print("\n--- QLearning on GraphEnv (target node 4) ---")
    env = GraphEnv(G, target_node=4, max_steps=20, step_penalty=-0.1)
    agent = QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n,
                           learning_rate=0.1, epsilon=0.3)
    results = train_agent(env, agent, episodes=50, verbose=True)
    print(f"Final average reward: {np.mean(results['episode_rewards'][-10:]):.2f}")

    # Test learned policy
    state, _ = env.reset()
    print("Test run:")
    for _ in range(10):
        action = agent.act(state, explore=False)
        state, reward, terminated, truncated, _ = env.step(action)
        print(f"  state {state}, reward {reward:.2f}")
        if terminated:
            print("  Reached target!")
            break

    # --- DQNAgent (if torch available) ---
    if HAS_TORCH:
        print("\n--- DQN on ResourceCollectionEnv ---")
        env = ResourceCollectionEnv(G, max_steps=20)
        # For DQN, we need flat observation vector
        state_dim = env.observation_space.shape[0]
        agent = DQNAgent(state_dim=state_dim, action_dim=env.action_space.n,
                         hidden_dim=16, epsilon=0.5, buffer_size=1000)
        results = train_dqn(env, agent, episodes=20, verbose=True)
        print(f"Final average reward: {np.mean(results['episode_rewards'][-5:]):.2f}")
    else:
        print("\nPyTorch not available – skipping DQN demo.")

    # --- GraphCoveringEnv with QLearning ---
    print("\n--- GraphCoveringEnv with QLearning ---")
    env = GraphCoveringEnv(G, max_steps=20)
    agent = QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n,
                           learning_rate=0.1, epsilon=0.3)
    results = train_agent(env, agent, episodes=50, verbose=True)
    print(f"Final average reward: {np.mean(results['episode_rewards'][-10:]):.2f}")

    # --- DeliveryEnv with QLearning ---
    print("\n--- DeliveryEnv with QLearning (pickup 0, delivery 4) ---")
    env = DeliveryEnv(G, pickup_node=0, delivery_node=4, max_steps=20)
    agent = QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n,
                           learning_rate=0.1, epsilon=0.3)
    results = train_agent(env, agent, episodes=50, verbose=True)
    print(f"Final average reward: {np.mean(results['episode_rewards'][-10:]):.2f}")


if __name__ == "__main__":
    demo()