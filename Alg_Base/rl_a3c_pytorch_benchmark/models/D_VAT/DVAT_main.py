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

from DVAT_envs import make_env,DVAT_ENV
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
        default=2,
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

    if args.New_Train:
        end_reward = False
    else:
        end_reward = True
        
    envs = [make_env(n_envs=args.workers,rank=i,end_reward=end_reward,log_dir=tensorboard_logdir) for i in range(args.workers)]
    vector_env = SubprocVectorEnv_TS(envs)

    action_space = DVAT_ENV.get_action_space()
    # policy = RandomPolicy(action_space=action_space)

    # buffer = VectorReplayBuffer(total_size=10000,buffer_num=args.workers)

    # collector = Collector(policy, vector_env, buffer)
    # collector.collect(n_step=1000,reset_before_collect=True)

    obs = vector_env.reset()
    test_obs_last1 = None
    test_obs_last2 = None
    while True:
        try:
            actions = np.random.randint(0, action_space.n, size=args.workers)
            results = vector_env.step(actions) # results.tuple:len(results) = 
            obs, reward, done, trunc, info = results
            ## Test done/reward
            # print(type(done)) #<class 'numpy.ndarray'>
            # print(type(reward)) #<class 'numpy.ndarray'>
            print(f"done: {done} reward: {reward}")

            ## Test Correctness of image
            # test_obs = obs[0]["actor_obs"]
            # if np.array_equal(test_obs_last1,test_obs[1]) and np.array_equal(test_obs_last2,test_obs[2]):
            #     print("Pass Test!!!!!!!!!!!!!")
            # else:
            #     print("NONONONONONONONONONONONONONONONONONONO")
            # import matplotlib.pyplot as plt
            # plt.subplot(1,3,1)
            # plt.imshow(test_obs[0].reshape(84,84,3))
            # plt.subplot(1,3,2)
            # plt.imshow(test_obs[1].reshape(84,84,3))
            # plt.subplot(1,3,3)
            # plt.imshow(test_obs[2].reshape(84,84,3))
            # plt.show()
            # test_obs_last1 = test_obs[0]
            # test_obs_last2 = test_obs[1]
        finally:
            simulator.terminate()
            try:
                simulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                simulator.kill()

def DVAT(args):

    simulator = subprocess.Popen(
        ["webots --no-rendering --mode=fast ../../Webots_Simulation/traffic_project/worlds/" + args.map],
        shell=True,
    )
    time.sleep(13)

    settings = {
        'n_timesteps': 1000000,
        'batch_size': 64,
        'buffer_size': 10000,
        'train_freq': 8,
    }

    # create parallel envs
    tensorboard_logdir = "./models/D_VAT/DVAT_logs"
    if tensorboard_logdir is None:
        os.makedirs(tensorboard_logdir)
    envs = [make_env(n_envs=args.workers,rank=i,end_reward=True,log_dir=tensorboard_logdir) for i in range(args.workers)]
    vector_env = SubprocVectorEnv_TS(envs)

    ## create policy
    action_space = DVAT_ENV.get_action_space()
    obs_space = DVAT_ENV.get_obs_space()
    actor_obs_space = obs_space["actor_obs"]
    critic_obs_space = obs_space["critic_obs"]
    
    sacd_policy = create_sacd_policy(actor_obs_space=actor_obs_space,action_space=action_space,obs_shape_critic=critic_obs_space.shape[0],action_shape=int(action_space.n))
    
    ## create buffer
    from tianshou.data import VectorReplayBuffer
    buffer = VectorReplayBuffer(total_size=settings["buffer_size"],buffer_num=args.workers)

    ## create collector
    from tianshou.data import Collector
    collector = Collector(sacd_policy, vector_env, buffer)
    collected_steps = 0

    # get device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    result = collector.collect(n_step=settings["train_freq"],reset_before_collect=True)
    # 训练循环，直到总步数达到 total_steps
    while collected_steps < settings["n_timesteps"]:
        try:
            # sample data from env
            result = collector.collect(n_step=settings["train_freq"])
            collected_steps += settings["train_freq"]

            # 从 buffer 中采样并更新策略
            batch_buffer,batch_indices = collector.buffer.sample(settings["batch_size"])

            # print(type(batch_buffer["act"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["done"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["terminated"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["truncated"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["obs"])) #<class 'tianshou.data.batch.Batch'>
            # print(type(batch_buffer["obs_next"])) #<class 'tianshou.data.batch.Batch'>
            # print(type(batch_buffer["rew"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["obs"]["actor_obs"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["obs"]["critic_obs"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["obs_next"]["actor_obs"])) #<class 'numpy.ndarray'>
            # print(type(batch_buffer["obs_next"]["critic_obs"])) #<class 'numpy.ndarray'>

            batch_buffer.act = torch.tensor(batch_buffer.act).to(device) if isinstance(batch_buffer.act, np.ndarray) else batch_buffer.act
            batch_buffer.obs = {k: torch.tensor(v).to(device) if isinstance(v, np.ndarray) else v for k, v in batch_buffer.obs.items()}
            batch_buffer.obs_next = {k: torch.tensor(v).to(device) if isinstance(v, np.ndarray) else v for k, v in batch_buffer.obs_next.items()}
            batch_buffer.rew = torch.tensor(batch_buffer.rew).to(device) if isinstance(batch_buffer.rew, np.ndarray) else batch_buffer.rew

            target_q = sacd_policy._target_q(collector.buffer, indices=batch_indices)
            losses = sacd_policy.learn(batch=batch_buffer,target_q=target_q)

        finally:
            simulator.terminate()
            try:
                simulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                simulator.kill()

if __name__ == "__main__":
    args = arg_config()
    # test_env(args)
    DVAT(args)



