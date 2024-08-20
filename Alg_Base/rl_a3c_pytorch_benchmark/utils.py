from __future__ import division
import numpy as np
import torch
import json
import logging
import math
import psutil
import sys


def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)


def read_config(file_path):
    """Read JSON config."""
    json_object = json.load(open(file_path, 'r'))
    return json_object


def norm_col_init(weights, std=1.0):
    x = torch.randn(weights.size())
    x *= std / torch.sqrt((x**2).sum(1, keepdim=True))
    return x


def ensure_shared_grads(model, shared_model, gpu=False):
    for param, shared_param in zip(model.parameters(),
                                   shared_model.parameters()):
        if shared_param.grad is not None and not gpu:
            return
        elif not gpu:
            shared_param._grad = param.grad
        else:
            shared_param._grad = param.grad.cpu()


def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        weight_shape = list(m.weight.data.size())
        fan_in = np.prod(weight_shape[1:4])
        fan_out = np.prod(weight_shape[2:4]) * weight_shape[0]
        w_bound = np.sqrt(6. / (fan_in + fan_out))
        m.weight.data.uniform_(-w_bound, w_bound)
        m.bias.data.fill_(0)
    elif classname.find('Linear') != -1:
        weight_shape = list(m.weight.data.size())
        fan_in = weight_shape[1]
        fan_out = weight_shape[0]
        w_bound = np.sqrt(6. / (fan_in + fan_out))
        m.weight.data.uniform_(-w_bound, w_bound)
        m.bias.data.fill_(0)

def clip_to_range(x, min_value=0, max_value=1):
    return max(min_value, min(x, max_value))

"""
    reward of baseline method: End-to-end
        reward = A - (sqrt(x^2+(y-d)^2)/c+lambda|w-w_0|)
"""
def get_E2E_reward(x:float,y:float,w:float,w_0:float,d_curr:float)->float:
    ## Hyperparams(Need to be determined after test)
    A = 1
    c = 1
    lamb = 1
    ## get reward
    dist = math.sqrt(math.pow(x,2)+math.pow(y-d_curr,2))
    w_abs = abs(w-w_0)
    reward = A-(dist/c+lamb*w_abs)
    return reward

"""
    reward of baseline method: DVAT
        reward = re-k_v*rv-ku*ru
"""
def get_DVAT_reward(A_fov:float,d_cmd:float,x:float,y:float,z:float,v:list,u:list,end_done:bool,discrete=True):
    ## Hyperparams
    beta = 1
    k_v = 0
    k_u = 0
    k_c = 20
    if not end_done:
        return -k_c
    else:
        ## get reward
        rx = max(0,1-abs(x-d_cmd))
        ry = max(0,1-abs(2/A_fov*math.atan(y/x)))
        if discrete:
            rz = 1
        else:
            rz = max(0,1-abs(2/A_fov*math.atan(z/x)))

        re = clip_to_range(math.pow(rx*ry*rz,beta))

        v_norm = math.sqrt(math.pow(v[0],2)+math.pow(v[1],2)+math.pow(v[2],2))
        rv = v_norm/(1+v_norm)
        u_norm = math.sqrt(math.pow(u[0],2)+math.pow(u[1],2)+math.pow(u[2],2))
        ru = u_norm/(1+u_norm)
        reward = re-k_v*rv-k_u*ru
        return reward

"""
    reward of baseline method: ENHANCE
        reward = A*r_rho*r_theta
"""
def get_ENHANCE_reward(rho:float,theta:float,rho_cmd:float,theta_cmd:float)->float:
    ## Hyperparams
    rho_max = 6 # determined after test
    theta_max = 0.785 # determined after test(90 degree)
    A = 1 # reward range: [0,1]
    ## get reward
    r_rho = max(0,1-abs(rho-rho_cmd)/rho_max)
    r_theta = max(0,1-abs(theta-theta_cmd)/theta_max)
    reward = A*r_rho*r_theta
    return reward

def check_memory_usage(threshold:float=0.85):
    memory_info = psutil.virtual_memory()

    # Get memory comsumption in percentage
    memory_usage = memory_info.percent

    print(f"Current memory usage: {memory_usage}%")

    if memory_usage > threshold*100:
        sys.exit(1)