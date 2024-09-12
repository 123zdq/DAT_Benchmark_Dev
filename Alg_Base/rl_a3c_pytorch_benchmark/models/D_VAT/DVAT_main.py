import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from tianshou.env import SubprocVectorEnv
from tianshou.policy import RandomPolicy
from tianshou.data import Collector, VectorReplayBuffer
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import gymnasium

from envs.gym_envs import make_env,UAV_VAT_Gymnasium
from envs.async_vecenv_ts import SubprocVectorEnv_TS
import subprocess, time
import argparse
from denseMlpPolicy import create_sacd_policy

# if __name__ == "__main__":
def arg_config():

    # --------------------------------------------------parameter-----------------------------------------------
    parse = argparse.ArgumentParser(description="run RPPO")
    parse.add_argument(
        "-w",
        "--workers",
        default=10,
        type=int,
        metavar="",
        help="the number of agents, default: 24",
    )
    parse.add_argument(
        "-t",
        "--train_mode",
        default=1,
        type=int,
        metavar="",
        help="whether to enable training mode, default: 1",
    )
    parse.add_argument(
        "-p",
        "--port",
        default=-1,
        type=int,
        metavar="",
        help="the communication port between the algorithm and the simulator, keep this parameter to default -1, it will automatically find an available port.",
    )
    parse.add_argument(
        "-params",
        "--savepath",
        default="params.pth",
        type=str,
        metavar="",
        help="model parameter filename, default: params.pth",
    )
    parse.add_argument(
        "-m",
        "--map",
        default="simpleway-grass_day.wbt",
        type=str,
        metavar="",
        help="the filename of map, default: citystreet-day.wbt",
    )
    parse.add_argument(
        "-tp",
        "--tensorboard_port",
        default=6006,
        type=int,
        metavar="",
        help="the port of tensorboard, recommended: 6006. Default is -1 (TensorBoard disabled). Set to any other value to enable TensorBoard, which will find an available port if needed.",
    )

    parse.add_argument(
        "-N",
        "--New_Train",
        action="store_true",
        default=False,
        help="whether restart a new training, default: False",
    )

    parse.add_argument(
        "-Len",
        "--observation_buffer_length",
        type=int,
        default=3,
        help="number of frame use for state",
    )
    args = parse.parse_args()

    if args.port == -1:
        import socket

        sock = socket.socket()
        sock.bind(("", 0))
        _, args.port = sock.getsockname()
        sock.close()

    import json

    # ------------------------------env_config.json--------------------------------
    with open(
        "../../Webots_Simulation/traffic_project/config/env_config.json", "r"
    ) as file:
        data = json.load(file)
    data["Config_Agen_Num_Port"] = args.port
    data["Simulation_Mode"] = "train"
    data["Tracker_Def"] = "DRONE"
    data["Sumo_Params"]["rou_update"] = True
    data["Verbose"] = False
    if args.train_mode == 1:
        data["Drone_Random_Config"]["direction_random"] = True
        data["Drone_Random_Config"]["horizon_bias_random"] = True
        data["Drone_Random_Config"]["verticle_bias_random"] = True
        data["Sumo_Params"]["fixed_seed"] = False
        data["Sumo_Params"]["fixed_car_group_num"] = False
        data["Reward_Config"]["view_range"] = 0.7
    else:
        data["Drone_Random_Config"]["direction_random"] = False
        data["Drone_Random_Config"]["horizon_bias_random"] = True
        data["Drone_Random_Config"]["horizon_bias_random_max"] = 6
        data["Drone_Random_Config"]["horizon_bias_random_min"] = 4
        data["Drone_Random_Config"]["verticle_bias_random"] = True
        data["Drone_Random_Config"]["verticle_bias_random_max"] = 6
        data["Drone_Random_Config"]["verticle_bias_random_min"] = 4
        data["Sumo_Params"]["fixed_color"] = False
        data["Sumo_Params"]["fixed_seed"] = True
        data["Sumo_Params"]["fixed_car_group_num"] = True
        
        data["Reward_Config"]["view_range"] = 1
    with open(
        "../../Webots_Simulation/traffic_project/config/env_config.json", "w"
    ) as file:
        json.dump(data, file, indent=4)

    # ------------------------------config.json--------------------------------
    with open("config.json", "r") as file:
        data = json.load(file)
    data["Benchmark"]["port_process"] = args.port
    data["Benchmark"]["auto_start"] = False
    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)

    if args.New_Train and os.path.exists("./PPO_logs/steps.txt"):
        with open("./PPO_logs/steps.txt", "w") as file:
            file.write("0")

    if args.train_mode == 1:
        Load_Model = not args.New_Train
    else:
        Load_Model = True

    return args

def test_env(args):

    # simulator !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    simulator = subprocess.Popen(
        ["webots ../../Webots_Simulation/traffic_project/worlds/" + args.map],
        shell=True,
    )
    time.sleep(13)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    tensorboard_logdir = "./models/D_VAT/DVAT_logs"
    if tensorboard_logdir is None:
        os.makedirs(tensorboard_logdir)

    envs = [make_env(n_envs=args.workers,rank=i,gym=False,end_reward=True,log_dir=tensorboard_logdir) for i in range(args.workers)]
    vector_env = SubprocVectorEnv_TS(envs)

    action_space = UAV_VAT_Gymnasium.get_action_space()
    # policy = RandomPolicy(action_space=action_space)

    # buffer = VectorReplayBuffer(total_size=10000,buffer_num=args.workers)

    # collector = Collector(policy, vector_env, buffer)
    # collector.collect(n_step=1000,reset_before_collect=True)

    obs = vector_env.reset()

    while True:
        try:
            actions = np.random.randint(0, action_space.n, size=args.workers)
            results = vector_env.step(actions) # results.tuple:len(results) = 
            obs, reward, done, trunc, info = results
        finally:
            simulator.terminate()
            try:
                simulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                simulator.kill()

def DVAT(args):
    settings = {'num_cpu': 6,
                'n_timesteps': 10000,
                'batch_size': 64,
                'buffer_size': 10000,
                'train_freq': 8,
                'WandB': False,  # True if you want to use wandb for logging
                'WandB_project': '<your_wandb_project>',
                'WandB_entity': '<your_wandb_entity>',
                'WandB_API_key': '<your_wandb_api_key>',
                'render': True,  # True to disable black screen
                'eval_episodes': 20,
                'eval_mode': True,  # True for model Test - False for Training
                'ts': 0.05,
                
                }

    # make parallel envs
    tensorboard_logdir = "./models/D_VAT/DVAT_logs"
    if tensorboard_logdir is None:
        os.makedirs(tensorboard_logdir)
    envs = [make_env(n_envs=args.workers,rank=i,gym=False,end_reward=True,log_dir=tensorboard_logdir) for i in range(args.workers)]
    vector_env = SubprocVectorEnv_TS(envs)

    # load config file
    import json
    with open("config.json", "r") as file:
        data = json.load(file)
    
    # make policy
    actor_obs_space = gymnasium.spaces.Box(
        low=0,
        high=1,
        shape=(args.observation_buffer_length,data["Benchmark"]["State_size"],data["Benchmark"]["State_size"],data["Benchmark"]["State_channel"]),
        dtype=np.float32
    )
    critic_obs_space = gymnasium.spaces.Box(-np.inf, np.inf, shape=(9,), dtype=np.float32)
    create_sacd_policy(observation_space=actor_obs_space,obs_shape_critic=9,action_shape=7)

if __name__ == "__main__":
    args = arg_config()
    test_env(args)



