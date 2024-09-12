from stable_baselines3.common.policies import BaseModel, BasePolicy
from typing import Any, Dict, List, Optional, Tuple, Type

from gymnasium import spaces
import torch as th
import torch.nn.functional as F
from torch.distributions import Categorical
from stable_baselines3.common.policies import BaseModel, BasePolicy
# from stable_baselines3.common.policies import register_policy
from stable_baselines3.common.preprocessing import get_action_dim
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
# from stable_baselines3.sac.policies import SACPolicy
from sacd.policies import SACDPolicy
from torch import nn
from customCNN import CustomCNN

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from utils import read_config

CFG_PATH = "./config.json"
cfg_json = read_config(CFG_PATH)
cfg_dict = cfg_json["Benchmark"]

OUTPUT_DIM = cfg_dict["Action_dim"]


class DenseMlp(nn.Module):
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dim: int = 256,
        n_layers: int = 2,
        squash_output: bool = False,
    ):
        super(DenseMlp, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.squash_output = squash_output
        self.layer_1 = nn.Linear(input_dim, hidden_dim)
        self.layer_2 = nn.Linear(hidden_dim, hidden_dim)
        if output_dim > 0:
            self.output_layer = nn.Linear(hidden_dim, output_dim)
        # for discrete setting no need for squash_output
        self.output_activation = nn.Identity()

    def forward(self, input_tensor: th.Tensor) -> th.Tensor:
        out_1 = F.relu(self.layer_1(input_tensor))
        # input_2 = th.cat([out_1, input_tensor], dim=1)
        out_2 = F.relu(self.layer_2(out_1))

        if self.output_dim < 0:
            return out_2

        # input_3 = th.cat([out_2, input_tensor], dim=1)
        out_3 = self.output_layer(out_2)

        if self.squash_output:
            out_3 = self.output_activation(out_3)
        return out_3

class DiscreteActor(BasePolicy):
    """
    Actor network (policy) for SACD

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param full_std: Whether to use (n_features x n_actions) parameters
        for the std instead of only (n_features,) when using gSDE.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    """

    action_space: spaces.Discrete

    def __init__(
        self,
        observation_space: spaces.Space,
        action_space: spaces.Box,
        net_arch: List[int],
        features_extractor: nn.Module,
        features_dim: int,
        activation_fn: Type[nn.Module] = nn.Softmax,
        use_sde: bool = False,
        log_std_init: float = -3,
        full_std: bool = True,
        use_expln: bool = False,
        clip_mean: float = 2.0,
        normalize_images: bool = True,
    ):
        super().__init__(
            observation_space,
            action_space,
            features_extractor=features_extractor,
            normalize_images=normalize_images,
            squash_output=False,
        )

        # Save arguments to re-create object at loading
        self.use_sde = use_sde
        self.sde_features_extractor = None
        self.net_arch = net_arch
        self.features_dim = features_dim
        self.activation_fn = activation_fn
        self.log_std_init = log_std_init
        self.use_expln = use_expln
        self.full_std = full_std
        self.clip_mean = clip_mean

        num_actions = self.action_space.n

        self.latent_pi = DenseMlp(features_dim, num_actions.item(), net_arch[0], squash_output=True)

        self.output_activation = nn.Softmax(dim=1)

    def _get_constructor_parameters(self) -> Dict[str, Any]:
        data = super()._get_constructor_parameters()

        data.update(
            dict(
                net_arch=self.net_arch,
                features_dim=self.features_dim,
                activation_fn=self.activation_fn,
                use_sde=self.use_sde,
                log_std_init=self.log_std_init,
                full_std=self.full_std,
                use_expln=self.use_expln,
                features_extractor=self.features_extractor,
                clip_mean=self.clip_mean,
            )
        )
        return data

    def forward(self, obs: th.Tensor, deterministic: bool = False) -> th.Tensor:
        features = self.extract_features(obs, self.features_extractor)

        action_probabilities = self.output_activation(self.latent_pi(features))

        if deterministic:
            action = th.argmax(action_probabilities)
        else:
            # random action according to policy
            dist = Categorical(probs=action_probabilities)
            action = dist.sample()

        return action

    def action_log_prob(self, obs: th.Tensor) -> Tuple[th.Tensor, th.Tensor]:
        features = self.extract_features(obs, self.features_extractor)
        action_prob = self.output_activation(self.latent_pi(features))

        # Have to deal with situation of 0.0 probabilities because we can't do log 0
        z = action_prob == 0.0
        z = z.float() * 1e-8
        log_action_prob = th.log(action_prob + z)
        return action_prob, log_action_prob

    def _predict(self, observation: th.Tensor, deterministic: bool = False) -> th.Tensor:
        return self.forward(observation, deterministic)


class DiscreteCritic(BaseModel):
    """
    Critic network(s) for DDPG/SAC/TD3.
    It represents the action-state value function (Q-value function).
    Compared to A2C/PPO critics, this one represents the Q-value
    and takes the continuous action as input. It is concatenated with the state
    and then fed to the network which outputs a single value: Q(s, a).
    For more recent algorithms like SAC/TD3, multiple networks
    are created to give different estimates.

    By default, it creates two critic networks used to reduce overestimation
    thanks to clipped Q-learning (cf TD3 paper).

    :param observation_space: Obervation space
    :param action_space: Action space
    :param net_arch: Network architecture
    :param features_extractor: Network to extract features
        (a CNN when using images, a nn.Flatten() layer otherwise)
    :param features_dim: Number of features
    :param activation_fn: Activation function
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether the features extractor is shared or not
        between the actor and the critic (this saves computation time)
    """

    action_space: spaces.Discrete

    def __init__(
        self,
        observation_space: spaces.Space,
        action_space: spaces.Discrete,
        net_arch: List[int],
        features_extractor: BaseFeaturesExtractor,
        features_dim: int,
        activation_fn: Type[nn.Module] = nn.ReLU,
        normalize_images: bool = True,
        n_critics: int = 2,
        share_features_extractor: bool = True,
    ):
        super().__init__(
            observation_space,
            action_space,
            features_extractor=features_extractor,
            normalize_images=normalize_images,
        )

        num_actions = self.action_space.n

        self.share_features_extractor = share_features_extractor
        self.n_critics = n_critics
        self.q_networks = []
        for idx in range(n_critics):
            q_net = DenseMlp(features_dim, num_actions.item(), net_arch[0])
            self.add_module(f"qf{idx}", q_net)
            self.q_networks.append(q_net)

    def get_crit_params(self, n):
        return self.q_networks[n].parameters()

    def forward(self, obs: th.Tensor) -> Tuple[th.Tensor, ...]:
        # Learn the features extractor using the policy loss only
        # when the features_extractor is shared with the actor
        if self.features_extractor is not None:
            with th.set_grad_enabled(not self.share_features_extractor):
                features = self.extract_features(obs, self.features_extractor)
        return tuple(q_net(features) for q_net in self.q_networks)

class SACDiscretePolicy(SACDPolicy):
    """
    Policy class (with both actor and critic) for SAC.
    :param observation_space: Observation space
    :param action_space: Action space
    :param lr_schedule: Learning rate schedule (could be constant)
    :param net_arch: The specification of the policy and value networks.
    :param activation_fn: Activation function
    :param use_sde: Whether to use State Dependent Exploration or not
    :param log_std_init: Initial value for the log standard deviation
    :param sde_net_arch: Network architecture for extracting features
        when using gSDE. If None, the latent features from the policy will be used.
        Pass an empty list to use the states as features.
    :param use_expln: Use ``expln()`` function instead of ``exp()`` when using gSDE to ensure
        a positive standard deviation (cf paper). It allows to keep variance
        above zero and prevent it from growing too fast. In practice, ``exp()`` is usually enough.
    :param clip_mean: Clip the mean output when using gSDE to avoid numerical instability.
    :param features_extractor_class: Features extractor to use.
    :param features_extractor_kwargs: Keyword arguments
        to pass to the features extractor.
    :param normalize_images: Whether to normalize images or not,
         dividing by 255.0 (True by default)
    :param optimizer_class: The optimizer to use,
        ``th.optim.Adam`` by default
    :param optimizer_kwargs: Additional keyword arguments,
        excluding the learning rate, to pass to the optimizer
    :param n_critics: Number of critic networks to create.
    :param share_features_extractor: Whether to share or not the features extractor
        between the actor and the critic (this saves computation time)
    """

    def __init__(self, *args, **kwargs):
        super(SACDiscretePolicy, self).__init__(
            *args,
            **kwargs,
        )
        # self.f_extractor = CustomCNN(obs_space)
        
    def make_actor(self, features_extractor: Optional[BaseFeaturesExtractor] = None) -> DiscreteActor:
        actor_kwargs = self.actor_kwargs
        if self.features_extractor is None:
            self.features_extractor = CustomCNN(actor_kwargs["observation_space"])
        actor_kwargs = self._update_features_extractor(actor_kwargs, self.features_extractor)
        actor_kwargs['features_dim'] = 512
        return DiscreteActor(**actor_kwargs).to(self.device)

    def make_critic(self, features_extractor: Optional[BaseFeaturesExtractor] = None) -> DiscreteCritic:
        critic_kwargs = self.critic_kwargs
        if self.features_extractor is None:
            self.features_extractor = CustomCNN(critic_kwargs["observation_space"])
        
        critic_kwargs = self._update_features_extractor(critic_kwargs, self.features_extractor)
        critic_kwargs['features_dim'] = 512
        return DiscreteCritic(**critic_kwargs).to(self.device)

    def forward(self, obs: th.Tensor, deterministic: bool = False) -> th.Tensor:
        return self._predict(obs, deterministic=deterministic)

    def _predict(self, observation: th.Tensor, deterministic: bool = False) -> th.Tensor:
        #observation = observation['actor']
        #print('shape observation', observation.shape)
        return self.actor(observation, deterministic)