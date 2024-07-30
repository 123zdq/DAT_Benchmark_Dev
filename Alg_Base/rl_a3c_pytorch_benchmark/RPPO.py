import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical
import os
import numpy as np

# import time


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer


class AC_RPPO(nn.Module):  # input_channels * 84 * 84
    def __init__(self, input_channels, hidden_width, action_dim):
        super().__init__()
        self.network = nn.Sequential(
            layer_init(nn.Conv2d(input_channels, 32, 5, padding=2)),
            nn.MaxPool2d(2, 2),
            nn.ReLU(),
            layer_init(nn.Conv2d(32, 32, 5, padding=1)),
            nn.MaxPool2d(2, 2),
            nn.ReLU(),
            layer_init(nn.Conv2d(32, 64, 4, padding=1)),
            nn.MaxPool2d(2, 2),
            nn.ReLU(),
            layer_init(nn.Conv2d(64, 64, 3, padding=1)),
            nn.MaxPool2d(2, 2),
            nn.ReLU(),
            nn.Flatten(),
        )

        self.lstm = nn.LSTM(1024, hidden_width)
        for name, param in self.lstm.named_parameters():
            if "bias" in name:
                nn.init.constant_(param, 0)
            elif "weight" in name:
                nn.init.orthogonal_(param, 1.0)

        self.actor = layer_init(nn.Linear(hidden_width, action_dim), std=0.01)
        self.critic = layer_init(nn.Linear(hidden_width, 1), std=1)

    def get_states(self, x, lstm_state, done):
        hidden = self.network(x)

        # LSTM logic
        batch_size = lstm_state[0].shape[1]
        hidden = hidden.view((-1, batch_size, self.lstm.input_size))
        done = done.view((-1, batch_size))
        new_hidden = []
        for h, d in zip(hidden, done):
            h, lstm_state = self.lstm(
                h.unsqueeze(0),
                (
                    (1.0 - d).view(self.lstm.num_layers, -1, 1) * lstm_state[0],
                    (1.0 - d).view(self.lstm.num_layers, -1, 1) * lstm_state[1],
                ),
            )
            new_hidden += [h]
        new_hidden = torch.flatten(torch.cat(new_hidden), 0, 1)
        return new_hidden, lstm_state

    def get_value(self, x, lstm_state, done):
        hidden, _ = self.get_states(x, lstm_state, done)
        return self.critic(hidden)

    def get_action_and_value(self, x, lstm_state, done, action=None):
        hidden, lstm_state = self.get_states(x, lstm_state, done)
        logits = self.actor(hidden)
        probs = Categorical(logits=logits)
        if action is None:
            action = probs.sample()
        return (
            action,
            probs.log_prob(action),
            probs.entropy(),
            self.critic(hidden),
            lstm_state,
        )


class UAV_RPPO_discrete:  # now:  torch base on GPU
    def __init__(self, **kwargs):
        self.device = torch.device("cuda")
        self.envs = None
        self.savepath = "params.pth"

        ####################################args for init
        self.input_channels = 3
        self.hidden_width = 64
        self.action_dim = 7

        ####################################args for train

        self.num_steps = 50
        self.num_envs = 4
        self.num_minibatches = 2  # factor of num_envs

        self.global_step = 0  # Initialization not supported !!!

        self.lr = 3e-4  # Learning rate
        self.gamma = 0.999  # Discount factor
        self.lamda = 0.95  # GAE parameter
        self.epsilon = 0.2  # PPO clip parameter
        self.K_epochs = 3  # PPO parameter
        self.entropy_coef = 0.01  # Entropy coefficient
        self.vloss_coef = 0.5
        self.max_grad_norm = 0.5

        ##################################

        for key, value in kwargs.items():
            setattr(self, key, value)

        if hasattr(self, "model") == False:
            self.model = AC_RPPO(
                self.input_channels, self.hidden_width, self.action_dim
            ).to(self.device)

        if os.path.exists(self.savepath):
            self.model.load_state_dict(torch.load(self.savepath))

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, eps=1e-5)

    def sample_update(self, next_lstm_state, next_state, next_done):  # modify

        # st=time.time()

        initial_lstm_state = (next_lstm_state[0].clone(), next_lstm_state[1].clone())

        obs = torch.zeros(
            (self.num_steps, self.num_envs) + (self.input_channels, 84, 84)
        ).to(self.device)

        actions = torch.zeros((self.num_steps, self.num_envs)).to(self.device)

        logprobs = torch.zeros((self.num_steps, self.num_envs)).to(self.device)
        rewards = torch.zeros((self.num_steps, self.num_envs)).to(self.device)
        dones = torch.zeros((self.num_steps, self.num_envs)).to(self.device)
        values = torch.zeros((self.num_steps, self.num_envs)).to(self.device)

        for step in range(self.num_steps):

            self.global_step += self.num_envs

            obs[step] = next_state
            dones[step] = next_done
            with torch.no_grad():
                action, logprob, _, value, next_lstm_state = (
                    self.model.get_action_and_value(
                        next_state, next_lstm_state, next_done
                    )
                )
                values[step] = value.view(-1)
            actions[step] = action
            logprobs[step] = logprob

            next_state, reward, done = self.envs.step(action.cpu().numpy())
            rewards[step] = torch.tensor(reward).to(self.device).view(-1)
            next_state, next_done = torch.Tensor(next_state).to(
                self.device
            ), torch.Tensor(done).to(self.device)

        torch.cuda.empty_cache()
        # print("train! ")###
        # print(time.time()-st)
        # st=time.time()

        # bootstrap value if not done
        with torch.no_grad():
            next_value = self.model.get_value(
                next_state,
                next_lstm_state,
                next_done,
            ).view(1, -1)

            advantages = torch.zeros_like(rewards).to(self.device)
            lastgaelam = 0
            for t in reversed(range(self.num_steps)):
                if t == self.num_steps - 1:
                    nextnonterminal = 1.0 - next_done
                    nextvalues = next_value
                else:
                    nextnonterminal = 1.0 - dones[t + 1]
                    nextvalues = values[t + 1]
                delta = (
                    rewards[t] + self.gamma * nextvalues * nextnonterminal - values[t]
                )
                advantages[t] = lastgaelam = (
                    delta + self.gamma * self.lamda * nextnonterminal * lastgaelam
                )
            returns = advantages + values

        obs = obs.view((-1,) + (self.input_channels, 84, 84))
        logprobs = logprobs.view(-1)
        actions = actions.view((-1,))
        dones = dones.view(-1)
        advantages = advantages.view(-1)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        returns = returns.view(-1)
        values = values.view(-1)

        assert self.num_envs % self.num_minibatches == 0
        envsperbatch = self.num_envs // self.num_minibatches
        envinds = np.arange(self.num_envs)
        flatinds = np.arange(self.num_steps * self.num_envs).reshape(
            self.num_steps, self.num_envs
        )
        for epoch in range(self.K_epochs):
            np.random.shuffle(envinds)
            for start in range(0, self.num_envs, envsperbatch):

                # print("minibatch  s")###

                end = start + envsperbatch
                mbenvinds = envinds[start:end]
                mb_inds = flatinds[
                    :, mbenvinds
                ].ravel()  # be really careful about the index

                _, newlogprob, entropy, newvalue, _ = self.model.get_action_and_value(
                    obs[mb_inds],
                    (
                        initial_lstm_state[0][:, mbenvinds],
                        initial_lstm_state[1][:, mbenvinds],
                    ),
                    dones[mb_inds],
                    actions.long()[mb_inds],
                )

                # print("minibatch  m")###

                logratio = newlogprob - logprobs[mb_inds]
                ratio = logratio.exp()

                mb_advantages = advantages[mb_inds]

                # Policy loss
                pg_loss1 = -mb_advantages * ratio
                pg_loss2 = -mb_advantages * torch.clamp(
                    ratio, 1 - self.epsilon, 1 + self.epsilon
                )
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                # Value loss
                newvalue = newvalue.view(-1)
                v_loss = 0.5 * ((newvalue - returns[mb_inds]) ** 2).mean()

                entropy_loss = entropy.mean()
                loss = (
                    pg_loss
                    - self.entropy_coef * entropy_loss
                    + v_loss * self.vloss_coef
                )

                # print("minibatch  t")###

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                self.optimizer.step()

        # print(time.time()-st)

        torch.save(self.model.state_dict(), self.savepath)
        return next_lstm_state, next_state, next_done

    def run(self):
        next_lstm_state = (
            torch.zeros(
                self.model.lstm.num_layers, self.num_envs, self.model.lstm.hidden_size
            ).to(self.device),
            torch.zeros(
                self.model.lstm.num_layers, self.num_envs, self.model.lstm.hidden_size
            ).to(self.device),
        )
        next_state = torch.Tensor(self.envs.reset()).to(self.device)
        next_done = torch.zeros(self.num_envs).to(self.device)
        while True:
            next_lstm_state, next_state, next_done = self.sample_update(
                next_lstm_state, next_state, next_done
            )


from envs import Envs, GE

workers = 5

agent = UAV_RPPO_discrete(
    envs=Envs(num_envs=workers, env_list=GE(workers), logs_show=True),
    num_envs=workers,
    num_minibatches=1,
    num_steps=50,
)
agent.run()
