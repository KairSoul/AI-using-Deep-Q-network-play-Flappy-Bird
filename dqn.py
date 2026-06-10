# dqn.py
import torch
import torch.nn as nn

class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super().__init__()

        self.network = nn.Sequential(
            # Layer 1
            nn.Linear(state_size, 128),
            nn.ReLU(),
            
            # Layer 2
            nn.Linear(128, 128),
            nn.ReLU(),
            
            # Output Layer
            nn.Linear(128, action_size)
        )

    def forward(self, x):
        return self.network(x)