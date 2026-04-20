"""
MULTI-AGENT REINFORCEMENT LEARNING ON GRAPHS – ULTIMATE IMPLEMENTATION
=======================================================================
This module provides multi‑agent reinforcement learning environments and agents
for graphs. It supports:

- Cooperative and competitive settings
- Graph‑based observations (local neighborhood) plus optional global information
- Multiple agents moving on a graph, with actions to move to neighboring nodes or stay
- Integration with PettingZoo for standard multi‑agent APIs
- Simple built‑in agents (Independent Q‑learning, DQN)
- Advanced multi‑agent algorithms: MADDPG (with discrete actions) and QMIX
- Optional integration with Ray/RLlib for scalable training
- Visualization of agent trajectories

All features degrade gracefully if required libraries are missing.
"""

import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from collections import defaultdict, deque
import copy

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# NetworkX for graph operations
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# Gymnasium / Gym for RL interfaces
try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYM = True
except ImportError:
    try:
        import gym
        from gym import spaces
        HAS_GYM = True
        gymnasium = gym  # alias
    except ImportError:
        HAS_GYM = False

# PettingZoo for multi-agent environments
try:
    from pettingzoo import ParallelEnv
    from pettingzoo.utils import parallel_to_aec
    HAS_PETTINGZOO = True
except ImportError:
    HAS_PETTINGZOO = False

# Ray / RLlib for scalable RL
try:
    import ray
    from ray.rllib.algorithms.ppo import PPOConfig
    from ray.rllib.algorithms.dqn import DQNConfig
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

# PyTorch for neural agents
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.distributions import Categorical
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Matplotlib for visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

logger = logging.getLogger(__name__)


# ============================================================================
# BASE ENVIRONMENT – MULTI-AGENT GRAPH ENVIRONMENT (with global observation)
# ============================================================================

class MultiAgentGraphEnv:
    """
    A multi‑agent environment on a graph.

    Agents move on the graph. Each agent occupies a node (or can be on the same node).
    Observation for each agent: local neighborhood (neighbors' node IDs, agent presence, etc.)
    Optionally, global information (positions of all agents) can be included.

    Action: move to a neighboring node or stay (action 0 = stay, action k = move to k-th neighbor).

    Can be cooperative (all agents share a reward) or competitive (each agent has own reward).
    """

    def __init__(
        self,
        graph: nx.Graph,
        n_agents: int,
        agent_positions: Optional[List[int]] = None,
        target_positions: Optional[List[int]] = None,
        cooperative: bool = True,
        max_steps: int = 100,
        observation_radius: int = 1,
        observation_type: str = "local",      # "local" or "global"
        reward_function: Optional[Callable] = None,
        collision_penalty: float = 0.0,
        seed: Optional[int] = None
    ):
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required for MultiAgentGraphEnv")
        self.graph = graph
        self.n_agents = n_agents
        self.max_steps = max_steps
        self.observation_radius = observation_radius
        self.cooperative = cooperative
        self.collision_penalty = collision_penalty
        self.seed = seed
        self.observation_type = observation_type
        np.random.seed(seed)

        # Agents' current positions
        if agent_positions is None:
            self.agent_positions = np.random.choice(list(graph.nodes()), size=n_agents, replace=True).tolist()
        else:
            self.agent_positions = agent_positions
        # Targets (optional, for reward)
        if target_positions is None:
            self.target_positions = [None] * n_agents
        else:
            self.target_positions = target_positions

        # Reward function: if None, use default based on reaching target
        if reward_function is None:
            self.reward_function = self._default_reward
        else:
            self.reward_function = reward_function

        # Action space: for each agent, number of possible moves = degree of current node + 1 (stay)
        self.max_degree = max(dict(graph.degree()).values())
        self.action_space_per_agent = self.max_degree + 1  # 0..max_degree, where 0 = stay, 1.. = neighbor index

        # Observation space
        self.local_obs_dim = 2 + self.max_degree  # [agent_id, current_node] + neighbors (padded)
        if observation_type == "global":
            # Add positions of all agents (n_agents integers)
            self.obs_dim = self.local_obs_dim + n_agents
        else:
            self.obs_dim = self.local_obs_dim

        self.observation_space_per_agent = spaces.Box(low=-1, high=graph.number_of_nodes()-1,
                                                       shape=(self.obs_dim,), dtype=np.int32)

        self.current_step = 0

    def _default_reward(self, agent_idx: int, state) -> float:
        """Default reward: +1 if agent reached its target, else 0."""
        if self.target_positions[agent_idx] is not None and \
           self.agent_positions[agent_idx] == self.target_positions[agent_idx]:
            return 1.0
        return 0.0

    def reset(self) -> Dict[int, np.ndarray]:
        """Reset environment and return initial observations for all agents."""
        self.current_step = 0
        if self.seed is not None:
            np.random.seed(self.seed)
        # Randomize positions if not fixed (could also implement custom reset logic)
        self.agent_positions = np.random.choice(list(self.graph.nodes()), size=self.n_agents, replace=True).tolist()
        return self._get_obs()

    def _get_obs(self) -> Dict[int, np.ndarray]:
        """Return observation for each agent."""
        obs = {}
        for i, pos in enumerate(self.agent_positions):
            # Local part: [agent_id, current_node, neighbors...]
            neighbors = list(self.graph.neighbors(pos))
            padded_neighbors = neighbors + [-1] * (self.max_degree - len(neighbors))
            local_obs = np.array([i, pos] + padded_neighbors, dtype=np.int32)

            if self.observation_type == "global":
                # Global part: positions of all agents (flattened)
                global_obs = np.array(self.agent_positions, dtype=np.int32)
                obs_i = np.concatenate([local_obs, global_obs])
            else:
                obs_i = local_obs
            obs[i] = obs_i
        return obs

    def step(self, actions: Dict[int, int]) -> Tuple[Dict[int, np.ndarray], Dict[int, float], bool, Dict]:
        """
        Take a step for all agents.

        Args:
            actions: dict mapping agent index -> action index.
                    Action 0 = stay; action 1.. = move to the k-th neighbor of current node.

        Returns:
            observations, rewards, done, info
        """
        self.current_step += 1
        rewards = {}
        info = defaultdict(dict)

        # Compute intended moves
        intended = []
        for i, pos in enumerate(self.agent_positions):
            neighbors = list(self.graph.neighbors(pos))
            act = actions.get(i, 0)
            if act == 0:
                new_pos = pos
            elif 1 <= act <= len(neighbors):
                new_pos = neighbors[act - 1]
            else:
                new_pos = pos  # invalid action, stay
            intended.append(new_pos)

        self.agent_positions = intended

        # Compute rewards
        for i in range(self.n_agents):
            rew = self.reward_function(i, self)
            if self.collision_penalty > 0 and intended.count(intended[i]) > 1:
                rew -= self.collision_penalty
            rewards[i] = rew

        # Check if done
        done = self.current_step >= self.max_steps

        # Optionally check if all agents reached targets
        if all(t is None or self.agent_positions[i] == t for i, t in enumerate(self.target_positions)):
            done = True

        obs = self._get_obs()
        return obs, rewards, done, info

    def render(self, mode='human'):
        """Simple textual render."""
        print(f"Step {self.current_step}: Positions: {self.agent_positions}")

    def close(self):
        pass


# ============================================================================
# PETTINGZOO WRAPPER (optional)
# ============================================================================

if HAS_PETTINGZOO:
    class PettingZooMultiAgentGraphEnv(ParallelEnv):
        """
        PettingZoo wrapper for MultiAgentGraphEnv.
        """

        def __init__(self, env: MultiAgentGraphEnv):
            super().__init__()
            self.env = env
            self.agents = [f"agent_{i}" for i in range(env.n_agents)]
            self.possible_agents = self.agents[:]
            self._action_spaces = {agent: spaces.Discrete(env.action_space_per_agent) for agent in self.agents}
            self._observation_spaces = {agent: env.observation_space_per_agent for agent in self.agents}

        def reset(self, seed=None, options=None):
            self.env.seed = seed
            obs = self.env.reset()
            return {f"agent_{i}": obs[i] for i in range(self.env.n_agents)}, {}

        def step(self, actions):
            env_actions = {int(agent.split('_')[1]): actions[agent] for agent in actions}
            obs, rewards, done, info = self.env.step(env_actions)
            petting_obs = {f"agent_{i}": obs[i] for i in range(self.env.n_agents)}
            petting_rewards = {f"agent_{i}": rewards[i] for i in range(self.env.n_agents)}
            dones = {agent: done for agent in self.agents}
            dones["__all__"] = done
            infos = {agent: {} for agent in self.agents}
            return petting_obs, petting_rewards, dones, infos

        def render(self):
            self.env.render()

        def close(self):
            self.env.close()

        def observation_space(self, agent):
            return self._observation_spaces[agent]

        def action_space(self, agent):
            return self._action_spaces[agent]


# ============================================================================
# BASE AGENT CLASS
# ============================================================================

class MultiAgentRLAgent:
    """Base class for multi‑agent RL agents."""

    def __init__(self, agent_id: int, action_space: int, observation_space: spaces.Box,
                 learning_rate: float = 0.1, discount: float = 0.95):
        self.agent_id = agent_id
        self.action_space = action_space
        self.observation_space = observation_space
        self.lr = learning_rate
        self.gamma = discount

    def act(self, observation: np.ndarray, explore: bool = True) -> int:
        """Select an action given observation."""
        raise NotImplementedError

    def learn(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool):
        """Update agent's policy/value function."""
        raise NotImplementedError


# ============================================================================
# INDEPENDENT Q-LEARNING AGENT
# ============================================================================

class IndependentQLearningAgent(MultiAgentRLAgent):
    """Tabular Q-learning agent with discretized observation."""

    def __init__(self, agent_id: int, action_space: int, observation_space: spaces.Box,
                 learning_rate: float = 0.1, discount: float = 0.95, epsilon: float = 0.1,
                 discretization_bins: int = 10):
        super().__init__(agent_id, action_space, observation_space, learning_rate, discount)
        self.epsilon = epsilon
        self.discretization_bins = discretization_bins
        # Q-table: mapping from (current_node) to array of action values
        self.q_table = {}  # mapping from (current_node) to array of action values

    def _discretize_obs(self, obs: np.ndarray) -> Tuple[int, ...]:
        """Convert observation to hashable state. Use only current node for simplicity."""
        return (int(obs[1]),)  # current node

    def act(self, observation: np.ndarray, explore: bool = True) -> int:
        state = self._discretize_obs(observation)
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.action_space)
        if explore and np.random.random() < self.epsilon:
            return np.random.randint(self.action_space)
        else:
            return int(np.argmax(self.q_table[state]))

    def learn(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool):
        state = self._discretize_obs(obs)
        next_state = self._discretize_obs(next_obs)
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.action_space)
        if next_state not in self.q_table:
            self.q_table[next_state] = np.zeros(self.action_space)
        target = reward
        if not done:
            target += self.gamma * np.max(self.q_table[next_state])
        self.q_table[state][action] += self.lr * (target - self.q_table[state][action])


# ============================================================================
# DEEP Q-NETWORK AGENT (PyTorch)
# ============================================================================

if HAS_TORCH:
    class DQNAgent(MultiAgentRLAgent):
        """Deep Q-Network agent with experience replay and target network."""

        def __init__(self, agent_id: int, action_space: int, observation_space: spaces.Box,
                     learning_rate: float = 1e-3, discount: float = 0.99, epsilon: float = 0.1,
                     hidden_size: int = 64, buffer_size: int = 10000, batch_size: int = 32,
                     target_update_freq: int = 100):
            super().__init__(agent_id, action_space, observation_space, learning_rate, discount)
            self.epsilon = epsilon
            self.batch_size = batch_size
            self.target_update_freq = target_update_freq
            self.step_count = 0

            # Neural network
            obs_dim = observation_space.shape[0]
            self.q_network = self._build_network(obs_dim, action_space, hidden_size)
            self.target_network = self._build_network(obs_dim, action_space, hidden_size)
            self.target_network.load_state_dict(self.q_network.state_dict())
            self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

            # Replay buffer
            self.replay_buffer = deque(maxlen=buffer_size)

        def _build_network(self, input_dim, output_dim, hidden_size):
            return nn.Sequential(
                nn.Linear(input_dim, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, output_dim)
            )

        def act(self, observation: np.ndarray, explore: bool = True) -> int:
            if explore and np.random.random() < self.epsilon:
                return np.random.randint(self.action_space)
            with torch.no_grad():
                obs_t = torch.FloatTensor(observation).unsqueeze(0)
                q_vals = self.q_network(obs_t).squeeze().numpy()
                return int(np.argmax(q_vals))

        def learn(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool):
            # Store experience
            self.replay_buffer.append((obs, action, reward, next_obs, done))

            # Sample batch
            if len(self.replay_buffer) < self.batch_size:
                return

            batch = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
            obs_batch = torch.FloatTensor([self.replay_buffer[i][0] for i in batch])
            action_batch = torch.LongTensor([self.replay_buffer[i][1] for i in batch])
            reward_batch = torch.FloatTensor([self.replay_buffer[i][2] for i in batch])
            next_obs_batch = torch.FloatTensor([self.replay_buffer[i][3] for i in batch])
            done_batch = torch.FloatTensor([self.replay_buffer[i][4] for i in batch])

            # Compute Q(s,a)
            q_values = self.q_network(obs_batch).gather(1, action_batch.unsqueeze(1)).squeeze()

            # Compute target Q(s',a')
            with torch.no_grad():
                next_q_values = self.target_network(next_obs_batch).max(1)[0]
                target = reward_batch + self.gamma * next_q_values * (1 - done_batch)

            loss = F.mse_loss(q_values, target)

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            self.step_count += 1
            if self.step_count % self.target_update_freq == 0:
                self.target_network.load_state_dict(self.q_network.state_dict())


# ============================================================================
# ADVANCED MULTI-AGENT ALGORITHMS (require PyTorch)
# ============================================================================

if HAS_TORCH:
    # ------------------------------------------------------------------------
    # MADDPG (Multi-Agent Deep Deterministic Policy Gradient) with discrete actions
    # ------------------------------------------------------------------------
    class MADDPGAgent:
        """
        A single agent for MADDPG. Holds actor and critic networks.
        This is meant to be used within a MADDPG trainer that coordinates updates.
        """
        def __init__(self, agent_id, obs_dim, action_dim, hidden_size=64, lr_actor=1e-4, lr_critic=1e-3):
            self.agent_id = agent_id
            self.obs_dim = obs_dim
            self.action_dim = action_dim

            # Actor: maps observation to action logits (for discrete actions)
            self.actor = nn.Sequential(
                nn.Linear(obs_dim, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, action_dim)
            )
            # Target actor
            self.actor_target = copy.deepcopy(self.actor)

            # Critic: maps concatenated (obs of all agents, actions of all agents) to Q-value
            # We'll build it externally because it needs to know total dimensions.
            self.critic = None   # to be set later
            self.critic_target = None

            self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr_actor)
            self.critic_optimizer = None   # set after critic created

        def set_critic(self, critic_net, critic_target):
            self.critic = critic_net
            self.critic_target = critic_target
            self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr_critic)

        def act(self, obs, explore=False, epsilon=0.1):
            """
            Returns action (int). If explore, uses epsilon-greedy with Gumbel-Softmax sampling.
            Otherwise takes argmax.
            """
            logits = self.actor(torch.FloatTensor(obs).unsqueeze(0)).squeeze()
            if explore:
                # Use Gumbel-Softmax for differentiable sampling during training, but here we just sample.
                # For simplicity, we do epsilon-greedy with softmax probabilities.
                if np.random.random() < epsilon:
                    return np.random.randint(self.action_dim)
                else:
                    probs = F.softmax(logits, dim=-1)
                    dist = Categorical(probs)
                    return dist.sample().item()
            else:
                return torch.argmax(logits).item()


    class MADDPG:
        """
        MADDPG trainer for discrete action spaces.
        Manages a set of agents, a replay buffer, and provides training step.
        """
        def __init__(self, env: MultiAgentGraphEnv, hidden_size=64, lr_actor=1e-4, lr_critic=1e-3,
                     buffer_size=int(1e6), batch_size=1024, gamma=0.99, tau=0.01):
            self.env = env
            self.n_agents = env.n_agents
            self.obs_dim = env.obs_dim
            self.action_dim = env.action_space_per_agent
            self.gamma = gamma
            self.tau = tau
            self.batch_size = batch_size

            # Create agents
            self.agents = []
            for i in range(self.n_agents):
                agent = MADDPGAgent(i, self.obs_dim, self.action_dim, hidden_size, lr_actor, lr_critic)
                self.agents.append(agent)

            # Build centralized critics for each agent (they share architecture but have separate networks)
            # Critic input: all observations (n_agents * obs_dim) + all actions (n_agents * action_dim)
            critic_input_dim = self.n_agents * (self.obs_dim + self.action_dim)
            for i in range(self.n_agents):
                critic = nn.Sequential(
                    nn.Linear(critic_input_dim, hidden_size),
                    nn.ReLU(),
                    nn.Linear(hidden_size, hidden_size),
                    nn.ReLU(),
                    nn.Linear(hidden_size, 1)
                )
                critic_target = copy.deepcopy(critic)
                self.agents[i].set_critic(critic, critic_target)

            # Replay buffer: stores (obs_dict, action_dict, reward_dict, next_obs_dict, done)
            self.replay_buffer = deque(maxlen=buffer_size)

        def store_transition(self, obs, actions, rewards, next_obs, done):
            """Store a transition in the replay buffer."""
            self.replay_buffer.append((obs, actions, rewards, next_obs, done))

        def sample_batch(self):
            """Sample a batch of transitions."""
            batch_indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
            batch = [self.replay_buffer[i] for i in batch_indices]
            # Convert to tensors
            obs_list = [torch.FloatTensor(np.array([b[0][i] for b in batch])) for i in range(self.n_agents)]
            action_list = [torch.LongTensor(np.array([b[1][i] for b in batch])) for i in range(self.n_agents)]
            reward_list = [torch.FloatTensor(np.array([b[2][i] for b in batch])) for i in range(self.n_agents)]
            next_obs_list = [torch.FloatTensor(np.array([b[3][i] for b in batch])) for i in range(self.n_agents)]
            done = torch.FloatTensor(np.array([b[4] for b in batch]))
            return obs_list, action_list, reward_list, next_obs_list, done

        def train_step(self):
            """Perform one update step for all agents."""
            if len(self.replay_buffer) < self.batch_size:
                return

            obs_list, action_list, reward_list, next_obs_list, done = self.sample_batch()

            # For each agent, compute critic loss and update
            for i, agent in enumerate(self.agents):
                # Build inputs for critic: concatenate all obs and all actions
                # obs_all: [batch_size, n_agents * obs_dim]
                obs_all = torch.cat(obs_list, dim=-1)   # shape: (batch, n_agents*obs_dim)
                # actions_all: one-hot encoded for each agent? For simplicity, we use integer actions.
                # But critic needs actions as input, we can either use one-hot or just the integer index.
                # In MADDPG with discrete actions, typically we one-hot encode. We'll do that.
                actions_onehot = []
                for a in range(self.n_agents):
                    actions_onehot.append(F.one_hot(action_list[a].long(), num_classes=self.action_dim).float())
                actions_all = torch.cat(actions_onehot, dim=-1)  # (batch, n_agents*action_dim)

                # Current Q value
                critic_input = torch.cat([obs_all, actions_all], dim=-1)
                q_val = agent.critic(critic_input).squeeze()

                # Target Q value: use target critic and target actors
                with torch.no_grad():
                    # Compute target actions from target actors
                    target_actions_onehot = []
                    for a in range(self.n_agents):
                        target_logits = self.agents[a].actor_target(next_obs_list[a])
                        # For discrete, we need to sample? In MADDPG they use Gumbel-Softmax for continuous relaxation.
                        # For simplicity, we take the argmax (deterministic) but that's not fully differentiable.
                        # We'll use Gumbel-Softmax to sample during training, but for target we can use argmax.
                        # Alternatively, we can use softmax directly as an approximation.
                        # We'll use softmax probabilities (not one-hot) as a continuous approximation.
                        probs = F.softmax(target_logits, dim=-1)  # (batch, action_dim)
                        target_actions_onehot.append(probs)
                    target_actions_all = torch.cat(target_actions_onehot, dim=-1)

                    # Next obs all
                    next_obs_all = torch.cat(next_obs_list, dim=-1)
                    target_critic_input = torch.cat([next_obs_all, target_actions_all], dim=-1)
                    target_q = agent.critic_target(target_critic_input).squeeze()
                    target_q = reward_list[i] + self.gamma * target_q * (1 - done)

                critic_loss = F.mse_loss(q_val, target_q)

                agent.critic_optimizer.zero_grad()
                critic_loss.backward()
                torch.nn.utils.clip_grad_norm_(agent.critic.parameters(), 0.5)
                agent.critic_optimizer.step()

                # Update actor using policy gradient
                # Actor loss = - Q(s, a) where a comes from current actor (using Gumbel-Softmax to keep differentiable)
                # We need to compute actions from current actor in a differentiable way.
                # We'll use Gumbel-Softmax to sample actions (reparameterized).
                # For simplicity, we use softmax probabilities as a continuous action.
                logits = agent.actor(obs_list[i])
                probs = F.gumbel_softmax(logits, tau=1, hard=False)  # (batch, action_dim)
                # Replace the i-th agent's action in the action_all with these probs
                # We need to reconstruct actions_all with the new probs for agent i, while keeping others as stored actions? No, we need to use current policy for agent i.
                # The actor loss is -Q(s, a) where a is from current policy, and Q is centralized critic.
                # We'll create a new actions_all with agent i's actions as probs, and others as stored actions (detached).
                actions_onehot_detached = []
                for a in range(self.n_agents):
                    if a == i:
                        actions_onehot_detached.append(probs)  # differentiable
                    else:
                        actions_onehot_detached.append(actions_onehot[a].detach())  # not updated
                actions_all_new = torch.cat(actions_onehot_detached, dim=-1)
                critic_input_new = torch.cat([obs_all, actions_all_new], dim=-1)
                q_val_new = agent.critic(critic_input_new).squeeze()
                actor_loss = -q_val_new.mean()

                agent.actor_optimizer.zero_grad()
                actor_loss.backward()
                torch.nn.utils.clip_grad_norm_(agent.actor.parameters(), 0.5)
                agent.actor_optimizer.step()

            # Soft update target networks
            for agent in self.agents:
                for target_param, param in zip(agent.actor_target.parameters(), agent.actor.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                for target_param, param in zip(agent.critic_target.parameters(), agent.critic.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)


    # ------------------------------------------------------------------------
    # QMIX (Mixing network for cooperative tasks)
    # ------------------------------------------------------------------------
    class QMIXAgent(nn.Module):
        """Agent network for QMIX: outputs Q-values given observation."""
        def __init__(self, obs_dim, action_dim, hidden_size=64):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(obs_dim, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, action_dim)
            )

        def forward(self, obs):
            return self.net(obs)


    class QMIX:
        """
        QMIX trainer for cooperative multi-agent tasks.
        Uses a mixing network to combine agent Q-values into a joint Q-value.
        """
        def __init__(self, env: MultiAgentGraphEnv, hidden_size=64, lr=1e-4,
                     buffer_size=int(1e6), batch_size=32, gamma=0.99, epsilon=1.0, epsilon_decay=0.995,
                     target_update_freq=200):
            self.env = env
            self.n_agents = env.n_agents
            self.obs_dim = env.obs_dim
            self.action_dim = env.action_space_per_agent
            self.gamma = gamma
            self.epsilon = epsilon
            self.epsilon_decay = epsilon_decay
            self.batch_size = batch_size
            self.target_update_freq = target_update_freq
            self.step_count = 0

            # Agent networks (one per agent, could be shared)
            self.agents = [QMIXAgent(self.obs_dim, self.action_dim, hidden_size) for _ in range(self.n_agents)]
            self.target_agents = [copy.deepcopy(agent) for agent in self.agents]

            # Mixing network: takes agent Q-values and global state, outputs total Q.
            # Global state here is the concatenation of all observations (or could be separate state).
            # We'll use concatenated observations as state.
            self.mixing_net = nn.Sequential(
                nn.Linear(self.n_agents * self.obs_dim + self.n_agents, hidden_size),  # plus agent Q-values? Actually Q-values are input separately.
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, 1)
            )
            self.target_mixing_net = copy.deepcopy(self.mixing_net)

            # Optimizer
            params = list(self.mixing_net.parameters())
            for agent in self.agents:
                params += list(agent.parameters())
            self.optimizer = optim.Adam(params, lr=lr)

            # Replay buffer: stores (obs_dict, action_dict, reward, next_obs_dict, done, state, next_state)
            self.replay_buffer = deque(maxlen=buffer_size)

        def store_transition(self, obs, actions, reward, next_obs, done):
            """Store a transition. Reward is scalar (cooperative)."""
            # state = concatenated obs of all agents
            state = np.concatenate([obs[i] for i in range(self.n_agents)])
            next_state = np.concatenate([next_obs[i] for i in range(self.n_agents)])
            self.replay_buffer.append((obs, actions, reward, next_obs, done, state, next_state))

        def act(self, obs, explore=True):
            """Return actions for all agents (dict)."""
            actions = {}
            for i, agent in enumerate(self.agents):
                if explore and np.random.random() < self.epsilon:
                    actions[i] = np.random.randint(self.action_dim)
                else:
                    with torch.no_grad():
                        obs_t = torch.FloatTensor(obs[i]).unsqueeze(0)
                        q_vals = agent(obs_t).squeeze().numpy()
                        actions[i] = int(np.argmax(q_vals))
            return actions

        def train_step(self):
            """Perform one training step."""
            if len(self.replay_buffer) < self.batch_size:
                return

            batch = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
            obs_list = []   # list of n_agents * (batch, obs_dim)
            actions_list = [] # list of n_agents * (batch,) actions
            rewards = []
            next_obs_list = []
            dones = []
            states = []
            next_states = []

            for b in batch:
                obs_b, actions_b, reward_b, next_obs_b, done_b, state_b, next_state_b = self.replay_buffer[b]
                if not obs_list:
                    obs_list = [[] for _ in range(self.n_agents)]
                    actions_list = [[] for _ in range(self.n_agents)]
                    next_obs_list = [[] for _ in range(self.n_agents)]
                for i in range(self.n_agents):
                    obs_list[i].append(obs_b[i])
                    actions_list[i].append(actions_b[i])
                    next_obs_list[i].append(next_obs_b[i])
                rewards.append(reward_b)
                dones.append(done_b)
                states.append(state_b)
                next_states.append(next_state_b)

            # Convert to tensors
            obs_t = [torch.FloatTensor(np.array(lst)) for lst in obs_list]
            actions_t = [torch.LongTensor(np.array(lst)) for lst in actions_list]
            next_obs_t = [torch.FloatTensor(np.array(lst)) for lst in next_obs_list]
            rewards_t = torch.FloatTensor(np.array(rewards))
            dones_t = torch.FloatTensor(np.array(dones))
            states_t = torch.FloatTensor(np.array(states))
            next_states_t = torch.FloatTensor(np.array(next_states))

            # Compute Q-values for each agent
            agent_qs = []
            target_agent_qs = []
            for i in range(self.n_agents):
                q = self.agents[i](obs_t[i])   # (batch, action_dim)
                # Select Q-values of taken actions
                q_taken = q.gather(1, actions_t[i].unsqueeze(1)).squeeze()
                agent_qs.append(q_taken)

                # Target Q-values: use target networks and select max action
                with torch.no_grad():
                    target_q = self.target_agents[i](next_obs_t[i])   # (batch, action_dim)
                    max_target_q = target_q.max(1)[0]   # (batch,)
                    target_agent_qs.append(max_target_q)

            # Mixing network: input agent_qs (n_agents, batch) and state
            agent_qs_stack = torch.stack(agent_qs, dim=1)   # (batch, n_agents)
            target_agent_qs_stack = torch.stack(target_agent_qs, dim=1)   # (batch, n_agents)

            # Mixing net takes state and agent_qs? In QMIX, mixing net takes agent Q-values and state, outputs joint Q.
            # We'll concatenate state and agent_qs.
            mix_input = torch.cat([states_t, agent_qs_stack], dim=-1)   # (batch, n_agents*obs_dim + n_agents)
            q_tot = self.mixing_net(mix_input).squeeze()

            # Target joint Q
            target_mix_input = torch.cat([next_states_t, target_agent_qs_stack], dim=-1)
            with torch.no_grad():
                q_tot_target = self.target_mixing_net(target_mix_input).squeeze()
                target = rewards_t + self.gamma * q_tot_target * (1 - dones_t)

            loss = F.mse_loss(q_tot, target)

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 10)
            self.optimizer.step()

            self.step_count += 1
            if self.step_count % self.target_update_freq == 0:
                for i in range(self.n_agents):
                    self.target_agents[i].load_state_dict(self.agents[i].state_dict())
                self.target_mixing_net.load_state_dict(self.mixing_net.state_dict())

            # Decay epsilon
            self.epsilon *= self.epsilon_decay


# ============================================================================
# MULTI-AGENT TRAINING LOOP (extended to handle advanced algorithms)
# ============================================================================

def train_multi_agent(
    env: MultiAgentGraphEnv,
    agents: Union[List[MultiAgentRLAgent], Any],  # can be list of simple agents or an advanced trainer
    episodes: int = 100,
    max_steps_per_episode: int = 100,
    render_every: Optional[int] = None,
    verbose: bool = True,
    advanced_mode: bool = False   # if True, agents is an advanced trainer object (MADDPG or QMIX)
) -> Dict[str, List[float]]:
    """
    Train multiple agents in the environment.

    For simple agents (each with act/learn), a standard loop is used.
    For advanced trainers (MADDPG, QMIX), the trainer must provide:
        - act(obs) returning actions dict
        - store_transition(obs, actions, rewards, next_obs, done)
        - train_step() called after each episode or step

    Returns:
        dict with keys 'episode_rewards' (list of total reward per episode) and
        'episode_lengths'.
    """
    episode_rewards = []
    episode_lengths = []

    for ep in range(episodes):
        obs = env.reset()
        total_reward = 0.0 if env.cooperative else np.zeros(env.n_agents)
        done = False
        step = 0
        while not done and step < max_steps_per_episode:
            if advanced_mode:
                actions = agents.act(obs, explore=True)
            else:
                actions = {}
                for i, agent in enumerate(agents):
                    actions[i] = agent.act(obs[i], explore=True)

            next_obs, rewards, done, info = env.step(actions)

            if advanced_mode:
                # Store transition in trainer's buffer
                if env.cooperative:
                    # For cooperative, reward is scalar; we need to pass total reward or per-agent?
                    # QMIX expects scalar reward (cooperative), MADDPG expects per-agent rewards.
                    # We'll assume the trainer knows how to handle it.
                    agents.store_transition(obs, actions, rewards, next_obs, done)
                else:
                    # For competitive, rewards is dict
                    agents.store_transition(obs, actions, rewards, next_obs, done)
            else:
                for i, agent in enumerate(agents):
                    agent.learn(obs[i], actions[i], rewards[i], next_obs[i], done)

            obs = next_obs
            if env.cooperative:
                total_reward += sum(rewards.values())   # assume all agents contribute to same total
            else:
                for i in range(env.n_agents):
                    total_reward[i] += rewards[i]
            step += 1
            if render_every is not None and ep % render_every == 0:
                env.render()

        if advanced_mode:
            # For QMIX/MADDPG, we might want to train after each episode
            if hasattr(agents, 'train_step'):
                agents.train_step()

        episode_rewards.append(total_reward)
        episode_lengths.append(step)

        if verbose and ep % 10 == 0:
            avg_reward = np.mean(total_reward) if isinstance(total_reward, (int, float)) else np.mean(total_reward)
            print(f"Episode {ep}, avg reward: {avg_reward:.2f}, length: {step}")

    return {'episode_rewards': episode_rewards, 'episode_lengths': episode_lengths}


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_trajectories(env: MultiAgentGraphEnv, trajectory: List[Dict[int, int]], filename: Optional[str] = None):
    """
    Plot agent trajectories on the graph.
    trajectory: list of agent positions per time step (list of dict agent->node)
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib not available – cannot plot trajectories")
        return
    pos = nx.spring_layout(env.graph)
    fig, ax = plt.subplots()
    nx.draw(env.graph, pos, ax=ax, node_color='lightgray', edge_color='gray')

    # Colors for agents
    colors = plt.cm.tab10(np.linspace(0, 1, env.n_agents))

    for t, positions in enumerate(trajectory):
        for agent, node in positions.items():
            x, y = pos[node]
            ax.scatter(x, y, color=colors[agent], s=100, alpha=0.7, label=f'Agent {agent}' if t == 0 else "")
            ax.annotate(str(agent), (x, y), fontsize=8, ha='center', va='center', color='white')

    ax.set_title("Agent Trajectories")
    ax.legend()
    if filename:
        plt.savefig(filename)
    else:
        plt.show()
    plt.close()


# ============================================================================
# RAY/RLLIB INTEGRATION (optional)
# ============================================================================

if HAS_RAY:
    from ray.rllib.env.multi_agent_env import MultiAgentEnv

    class RLLibMultiAgentGraphEnv(MultiAgentEnv):
        """RLlib wrapper for MultiAgentGraphEnv."""

        def __init__(self, env_config):
            super().__init__()
            graph = env_config.get('graph')
            n_agents = env_config.get('n_agents', 2)
            self.env = MultiAgentGraphEnv(graph=graph, n_agents=n_agents, **env_config)
            self._agent_ids = [f"agent_{i}" for i in range(n_agents)]
            self.observation_space = self.env.observation_space_per_agent
            self.action_space = spaces.Discrete(self.env.action_space_per_agent)

        def reset(self, *, seed=None, options=None):
            obs = self.env.reset()
            return {f"agent_{i}": obs[i] for i in range(self.env.n_agents)}, {}

        def step(self, action_dict):
            env_actions = {int(agent.split('_')[1]): action_dict[agent] for agent in action_dict}
            obs, rewards, done, info = self.env.step(env_actions)
            rllib_obs = {f"agent_{i}": obs[i] for i in range(self.env.n_agents)}
            rllib_rewards = {f"agent_{i}": rewards[i] for i in range(self.env.n_agents)}
            rllib_dones = {f"agent_{i}": done for i in range(self.env.n_agents)}
            rllib_dones["__all__"] = done
            return rllib_obs, rllib_rewards, rllib_dones, info

        def render(self):
            self.env.render()


# ============================================================================
# DEMO (updated to show new features)
# ============================================================================

def demo():
    """Run a simple multi-agent demo with Independent Q-learning."""
    if not HAS_NETWORKX:
        print("NetworkX required for demo.")
        return
    # Create a small graph
    G = nx.cycle_graph(5)
    env = MultiAgentGraphEnv(graph=G, n_agents=2, max_steps=20, cooperative=True, observation_type="global")

    # Create agents (Independent Q-learning)
    agents = [
        IndependentQLearningAgent(
            agent_id=i,
            action_space=env.action_space_per_agent,
            observation_space=env.observation_space_per_agent,
            learning_rate=0.1,
            epsilon=0.1
        )
        for i in range(env.n_agents)
    ]

    # Train
    results = train_multi_agent(env, agents, episodes=100, verbose=True)
    print("Training completed.")

    # Test a trajectory
    obs = env.reset()
    trajectory = [{i: env.agent_positions[i] for i in range(env.n_agents)}]
    done = False
    while not done:
        actions = {i: agents[i].act(obs[i], explore=False) for i in range(env.n_agents)}
        obs, rewards, done, _ = env.step(actions)
        trajectory.append({i: env.agent_positions[i] for i in range(env.n_agents)})
    plot_trajectories(env, trajectory)


if __name__ == "__main__":
    demo()