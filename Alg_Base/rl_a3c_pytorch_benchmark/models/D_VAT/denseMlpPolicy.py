import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

import torch
import torch.nn as nn
import torch.nn.functional as F
import gymnasium
from tianshou.data import Batch
from tianshou.policy import DiscreteSACPolicy
from tianshou.utils.net.common import Net
from tianshou.utils.net.continuous import ActorProb
from torch.optim import Adam
from customCNN import CustomCNN

class DenseMlp(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=256, squash_output=True):
        super(DenseMlp, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.squash_output = squash_output
        self.layer_1 = nn.Linear(input_dim, hidden_dim)
        self.layer_2 = nn.Linear(hidden_dim, hidden_dim)
        self.output_layer = nn.Linear(hidden_dim, output_dim)
        self.output_activation = nn.Softmax(dim=-1) if squash_output else nn.Identity()

    def forward(self, x):
        out_1 = F.relu(self.layer_1(x))
        # input_2 = th.cat([out_1, input_tensor], dim=1)
        out_2 = F.relu(self.layer_2(out_1))
        x = self.output_layer(out_2)
        return self.output_activation(x)

class CustomDiscreteActor(nn.Module):
    """
    自定义的离散动作空间的Actor网络。
    """
    def __init__(self, observation_space:gymnasium.spaces.Box, action_dim:int, hidden_sizes=(256,)):
        super().__init__()
        self.feature_extractor = CustomCNN(observation_space)
        feature_dim = self.feature_extractor.linear[-2].out_features
        self.net = DenseMlp(feature_dim, action_dim, hidden_dim=hidden_sizes[0])

    def forward(self, obs, state=None, info={}):
        features = self.feature_extractor(obs)
        logits = self.net(features)
        return logits, state

class CustomDiscreteCritic(nn.Module):
    """
    自定义的离散动作空间的Critic网络。
    """
    def __init__(self, obs_shape_critic, action_shape, hidden_sizes=(256,)):
        super().__init__()
        self.net = DenseMlp(obs_shape_critic, action_shape, hidden_dim=hidden_sizes[0])

    def forward(self, obs):
        q_values = self.net(obs)
        return q_values

# To DO:修改成能够兼容非对称的版本
# 创建自定义的ActorCritic网络和SAC Policy
def create_sacd_policy(observation_space, obs_shape_critic, action_shape, lr=3e-4, gamma=0.99, tau=0.005, alpha=0.2)->DiscreteSACPolicy:
    # 定义actor和critic
    actor = CustomDiscreteActor(observation_space, action_shape)
    critic1 = CustomDiscreteCritic(obs_shape_critic, action_shape)
    critic2 = CustomDiscreteCritic(obs_shape_critic, action_shape)

    # 定义优化器
    actor_optim = Adam(actor.parameters(), lr=lr)
    critic1_optim = Adam(critic1.parameters(), lr=lr)
    critic2_optim = Adam(critic2.parameters(), lr=lr)

    # 创建离散SAC Policy
    sacd_policy = DiscreteSACPolicy(
        actor=actor,
        actor_optim=actor_optim,
        critic1=critic1,
        critic1_optim=critic1_optim,
        critic2=critic2,
        critic2_optim=critic2_optim,
        tau=tau,
        gamma=gamma,
        alpha=alpha
    )

    return sacd_policy

