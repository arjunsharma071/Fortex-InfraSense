# models/intervention_agent.py
"""
Reinforcement Learning agent for infrastructure intervention selection
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque
import random


class InterventionAgent:
    """
    Reinforcement Learning agent that learns optimal infrastructure interventions
    State: Road segment features + network context
    Action: Type of intervention (widen, flyover, bridge, etc.)
    Reward: Reduction in stress index + cost efficiency
    """
    
    def __init__(self, state_dim=50, action_dim=5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Q-Network
        self.q_network = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )
        
        # Policy Network
        self.policy_network = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Softmax(dim=1)
        )
        
        # Optimizer
        self.optimizer = torch.optim.Adam(
            list(self.q_network.parameters()) + list(self.policy_network.parameters()),
            lr=0.001
        )
        
    def get_action(self, state, epsilon=0.1):
        """
        Epsilon-greedy action selection
        """
        if np.random.random() < epsilon:
            return np.random.choice(self.action_dim)
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.q_network(state_tensor)
                return torch.argmax(q_values).item()
    
    def calculate_reward(self, state, action, next_state):
        """
        Multi-objective reward function
        """
        # 1. Stress reduction
        stress_reduction = state.get('isi', 0.5) - next_state.get('isi', 0.5)
        
        # 2. Cost efficiency (higher reward for cheaper interventions)
        cost = self._get_intervention_cost(action)
        cost_efficiency = 1.0 / (cost + 1e-6)
        
        # 3. Network effect (impact on surrounding roads)
        network_effect = self._calculate_network_impact(state, action)
        
        # 4. Long-term sustainability
        sustainability = self._calculate_sustainability(action)
        
        # Combined reward
        reward = (
            0.4 * stress_reduction +
            0.3 * cost_efficiency +
            0.2 * network_effect +
            0.1 * sustainability
        )
        
        return reward
    
    def _get_intervention_cost(self, action):
        """
        Estimated costs for different interventions (in million $ per km)
        """
        cost_map = {
            0: 0.5,    # Minor repairs
            1: 2.0,    # Road widening
            2: 15.0,   # Flyover construction
            3: 25.0,   # Bridge construction
            4: 0.2     # Traffic management
        }
        return cost_map.get(action, 1.0)
    
    def _calculate_network_impact(self, state, action):
        """Calculate impact on surrounding road network"""
        # Simplified network impact calculation
        base_impact = 0.1
        if action in [1, 2, 3]:  # Major interventions
            base_impact = 0.3
        return base_impact
    
    def _calculate_sustainability(self, action):
        """Calculate long-term sustainability of intervention"""
        sustainability_map = {
            0: 0.3,    # Minor repairs - short term
            1: 0.7,    # Road widening - medium term
            2: 0.9,    # Flyover - long term
            3: 0.95,   # Bridge - very long term
            4: 0.5     # Traffic management - needs updates
        }
        return sustainability_map.get(action, 0.5)
    
    def update(self, batch):
        """Update Q-network using batch of experiences"""
        states, actions, rewards, next_states, dones = batch
        
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # Current Q values
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Target Q values
        with torch.no_grad():
            next_q = self.q_network(next_states).max(1)[0]
            target_q = rewards + 0.99 * next_q * (1 - dones)
        
        # Loss and update
        loss = F.mse_loss(current_q.squeeze(), target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()


class ReplayBuffer:
    """Experience replay buffer for RL training"""
    
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones)
        )
    
    def __len__(self):
        return len(self.buffer)


class InterventionEnvironment:
    """
    Simulated environment for training the intervention agent
    """
    
    def __init__(self, road_data):
        self.road_data = road_data
        self.current_segment = 0
        self.max_steps = 100
        self.step_count = 0
        
    def reset(self):
        """Reset environment to initial state"""
        self.current_segment = np.random.randint(0, len(self.road_data))
        self.step_count = 0
        return self._get_state()
    
    def step(self, action):
        """Execute action and return next state, reward, done"""
        current_state = self._get_state()
        
        # Simulate intervention effect
        next_state = self._simulate_intervention(action)
        
        # Calculate reward
        reward = self._calculate_reward(current_state, action, next_state)
        
        self.step_count += 1
        done = self.step_count >= self.max_steps
        
        return next_state, reward, done
    
    def _get_state(self):
        """Get current state representation"""
        segment = self.road_data[self.current_segment]
        return {
            'isi': segment.get('stress_index', 0.5),
            'congestion': segment.get('congestion_score', 0.5),
            'safety': segment.get('safety_score', 0.5),
            'features': np.random.randn(50)  # Placeholder features
        }
    
    def _simulate_intervention(self, action):
        """Simulate the effect of an intervention"""
        current = self._get_state()
        
        # Intervention effects
        effects = {
            0: {'isi': -0.05, 'congestion': -0.03},  # Minor repairs
            1: {'isi': -0.15, 'congestion': -0.20},  # Road widening
            2: {'isi': -0.25, 'congestion': -0.30},  # Flyover
            3: {'isi': -0.30, 'congestion': -0.25},  # Bridge
            4: {'isi': -0.10, 'congestion': -0.15},  # Traffic management
        }
        
        effect = effects.get(action, {'isi': 0, 'congestion': 0})
        
        return {
            'isi': max(0, current['isi'] + effect['isi']),
            'congestion': max(0, current['congestion'] + effect['congestion']),
            'safety': current['safety'],
            'features': current['features']
        }
    
    def _calculate_reward(self, state, action, next_state):
        """Calculate reward for intervention"""
        stress_reduction = state['isi'] - next_state['isi']
        cost_factor = 1.0 / (self._get_cost(action) + 1)
        return stress_reduction * 10 + cost_factor
    
    def _get_cost(self, action):
        """Get intervention cost"""
        costs = [0.5, 2.0, 15.0, 25.0, 0.2]
        return costs[action] if action < len(costs) else 1.0
