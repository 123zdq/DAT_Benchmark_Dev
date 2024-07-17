from __future__ import division
import torch
import torch.nn as nn
import torch.nn.functional as F
from utils import norm_col_init, weights_init


class A3Clstm(torch.nn.Module):
    def __init__(self, num_inputs, action_dim, args):
        super(A3Clstm, self).__init__()
        self.hidden_size = args.hidden_size
        self.conv1 = nn.Conv2d(num_inputs, 32, 5, stride=1, padding=2)
        self.conv2 = nn.Conv2d(32, 32, 5, stride=1, padding=1)
        self.conv3 = nn.Conv2d(32, 64, 4, stride=1, padding=1)
        self.conv4 = nn.Conv2d(64, 64, 3, stride=1, padding=1)

        self.previlege_state = args.previlege_state
        if not self.previlege_state:
            self.extra_fcn_dim = 0
        else:
            self.extra_fcn_dim = args.previlege_state_dim

        self.lstm = nn.LSTMCell(1024, self.hidden_size)
        num_outputs = action_dim
        self.critic_linear = nn.Linear(self.hidden_size+self.extra_fcn_dim, 1)
        self.actor_linear = nn.Linear(self.hidden_size+self.extra_fcn_dim, num_outputs)

        relu_gain = nn.init.calculate_gain("relu")
        self.conv1.weight.data.mul_(relu_gain)
        self.conv1.bias.data.fill_(0)
        self.conv2.weight.data.mul_(relu_gain)
        self.conv2.bias.data.fill_(0)
        self.conv3.weight.data.mul_(relu_gain)
        self.conv3.bias.data.fill_(0)
        self.conv4.weight.data.mul_(relu_gain)
        self.conv4.bias.data.fill_(0)
        self.actor_linear.weight.data = norm_col_init(
            self.actor_linear.weight.data, 0.01
        )
        self.actor_linear.bias.data.fill_(0)
        self.critic_linear.weight.data = norm_col_init(
            self.critic_linear.weight.data, 1.0
        )
        self.critic_linear.bias.data.fill_(0)

        for name, p in self.named_parameters():
            if "lstm" in name:
                if "weight_ih" in name:
                    nn.init.xavier_uniform_(p.data)
                elif "weight_hh" in name:
                    nn.init.orthogonal_(p.data)
                elif "bias_ih" in name:
                    p.data.fill_(0)
                    # Set forget-gate bias to 1
                    n = p.size(0)
                    p.data[(n // 4) : (n // 2)].fill_(1)
                elif "bias_hh" in name:
                    p.data.fill_(0)

        self.train()

    def forward(self, inputs, hx, cx,previlege_state_dict=None):
        x = F.relu(F.max_pool2d(self.conv1(inputs), 2, 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv3(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv4(x), 2, 2))

        x = x.view(x.size(0), -1)

        hx, cx = self.lstm(x, (hx, cx))
        if self.previlege_state:
            x = torch.cat((hx,previlege_state_dict),dim=1)
            print(x.shape)
        else:
            x = hx
        # print("shape of x is:",x.shape) # (1,256)
        return self.critic_linear(x), self.actor_linear(x), hx, cx

class A3ClstmE2E(torch.nn.Module):
    def __init__(self, num_inputs, action_dim, args):
        super(A3Clstm, self).__init__()
        self.hidden_size = args.hidden_size
        self.conv1 = nn.Conv2d(num_inputs, 32, 5, stride=1, padding=2)
        self.conv2 = nn.Conv2d(32, 32, 5, stride=1, padding=1)
        self.conv3 = nn.Conv2d(32, 64, 4, stride=1, padding=1)
        self.conv4 = nn.Conv2d(64, 64, 3, stride=1, padding=1)

        self.lstm = nn.LSTMCell(1024, self.hidden_size)
        
        num_outputs = action_dim
        self.critic_linear = nn.Linear(self.hidden_size, 1)
        self.actor_linear = nn.Linear(self.hidden_size, num_outputs)
        layers = [self.conv1,self.conv2,self.conv3,self.conv4]
        self.init_params(layers)
        self.train()

    def forward(self, inputs, hx, cx):
        x = F.relu(F.max_pool2d(self.conv1(inputs), 2, 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv3(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv4(x), 2, 2))

        x = x.view(x.size(0), -1)
        hx, cx = self.lstm(x, (hx, cx))

        x = hx
        
        return self.critic_linear(x), self.actor_linear(x), hx, cx

    """
        init_params:
        Input:
            layers: A list of all the Conv Layers
        Output: Void
    """
    def init_params(self,layers):
        # Init the Params of Conv Module
        relu_gain = nn.init.calculate_gain("relu")
        for layer in layers:
            if isinstance(layer,nn.Conv2d):
                layer.weight.data.mul_(relu_gain)
                layer.bias.data.fill_(0)

        # Init the Params of Linear Module
        self.actor_linear.weight.data = norm_col_init(self.actor_linear.weight.data, 0.01)
        self.actor_linear.bias.data.fill_(0)
        self.critic_linear.weight.data = norm_col_init(self.critic_linear.weight.data, 1.0)
        self.critic_linear.bias.data.fill_(0)

        # Init the Params of LSTM Module
        for name, p in self.named_parameters():
            if "lstm" in name:
                if "weight_ih" in name:
                    nn.init.xavier_uniform_(p.data)
                elif "weight_hh" in name:
                    nn.init.orthogonal_(p.data)
                elif "bias_ih" in name:
                    p.data.fill_(0)
                    # Set forget-gate bias to 1
                    n = p.size(0)
                    p.data[(n // 4) : (n // 2)].fill_(1)
                elif "bias_hh" in name:
                    p.data.fill_(0)

class A3ClstmADVOT(torch.nn.Module):
    def __init__(self, num_inputs, action_dim, args):
        super(A3Clstm, self).__init__()
        self.hidden_size = args.hidden_size
        self.conv1 = nn.Conv2d(num_inputs, 32, 5, stride=1, padding=2)
        self.conv2 = nn.Conv2d(32, 32, 5, stride=1, padding=1)
        self.conv3 = nn.Conv2d(32, 64, 4, stride=1, padding=1)
        self.conv4 = nn.Conv2d(64, 64, 3, stride=1, padding=1)

        self.lstm = nn.LSTMCell(1024, self.hidden_size)
        num_outputs = action_dim
        self.critic_linear = nn.Linear(self.hidden_size, 1)
        self.actor_linear = nn.Linear(self.hidden_size, num_outputs)
        layers = [self.conv1,self.conv2,self.conv3,self.conv4]
        self.init_params(layers)
        self.train()

    def forward(self, inputs, hx, cx):
        x = F.relu(F.max_pool2d(self.conv1(inputs), 2, 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv3(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv4(x), 2, 2))

        x = x.view(x.size(0), -1)

        hx, cx = self.lstm(x, (hx, cx))

        x = hx

        return self.critic_linear(x), self.actor_linear(x), hx, cx

    """
        init_params:
        Input:
            layers: A list of all the Conv Layers
        Output: Void
    """
    def init_params(self,layers):
        # Init the Params of Conv Module
        relu_gain = nn.init.calculate_gain("relu")
        for layer in layers:
            if isinstance(layer,nn.Conv2d):
                layer.weight.data.mul_(relu_gain)
                layer.bias.data.fill_(0)

        # Init the Params of Linear Module
        self.actor_linear.weight.data = norm_col_init(self.actor_linear.weight.data, 0.01)
        self.actor_linear.bias.data.fill_(0)
        self.critic_linear.weight.data = norm_col_init(self.critic_linear.weight.data, 1.0)
        self.critic_linear.bias.data.fill_(0)

        # Init the Params of LSTM Module
        for name, p in self.named_parameters():
            if "lstm" in name:
                if "weight_ih" in name:
                    nn.init.xavier_uniform_(p.data)
                elif "weight_hh" in name:
                    nn.init.orthogonal_(p.data)
                elif "bias_ih" in name:
                    p.data.fill_(0)
                    # Set forget-gate bias to 1
                    n = p.size(0)
                    p.data[(n // 4) : (n // 2)].fill_(1)
                elif "bias_hh" in name:
                    p.data.fill_(0)